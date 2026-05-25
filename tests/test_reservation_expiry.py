from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models.enums import ReservationStatus
from app.models.item import CreateItemRequest
from app.models.reservation import CreateReservationRequest
from app.repositories.in_memory.item_repo import InMemoryItemRepository
from app.repositories.in_memory.reservation_repo import InMemoryReservationRepository
from app.services.item_service import ItemService
from app.services.reservation_service import ReservationService


def _past(seconds: int = 60) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


def _future(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


@pytest.fixture
def item_service():
    return ItemService(repository=InMemoryItemRepository())


@pytest.fixture
def reservation_service(item_service):
    return ReservationService(
        repository=InMemoryReservationRepository(),
        item_service=item_service,
    )


@pytest.fixture
def item(item_service):
    return item_service.create_item(
        CreateItemRequest(name="Widget", sku="WGT-001", total_quantity=50)
    )


# ── lazy auto-expire on get ────────────────────────────────────────────────────

def test_get_expired_pending_auto_cancels(reservation_service, item):
    res = reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=10, requester_id="u1", expires_at=_past()
        )
    )
    fetched = reservation_service.get_reservation(res.id)
    assert fetched.status == ReservationStatus.CANCELLED


def test_get_expired_pending_releases_reserved_quantity(reservation_service, item_service, item):
    res = reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=10, requester_id="u1", expires_at=_past()
        )
    )
    reservation_service.get_reservation(res.id)
    avail = item_service.get_availability(item.id)
    assert avail.reserved_quantity == 0
    assert avail.available_quantity == 50


def test_get_expired_confirmed_auto_cancels(reservation_service, item):
    res = reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u1", expires_at=_past()
        )
    )
    reservation_service.confirm_reservation(res.id)
    fetched = reservation_service.get_reservation(res.id)
    assert fetched.status == ReservationStatus.CANCELLED


def test_get_not_yet_expired_leaves_status_unchanged(reservation_service, item):
    res = reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u1", expires_at=_future()
        )
    )
    fetched = reservation_service.get_reservation(res.id)
    assert fetched.status == ReservationStatus.PENDING


def test_get_no_expiry_leaves_status_unchanged(reservation_service, item):
    res = reservation_service.create_reservation(
        CreateReservationRequest(item_id=item.id, quantity=5, requester_id="u1")
    )
    fetched = reservation_service.get_reservation(res.id)
    assert fetched.status == ReservationStatus.PENDING


def test_get_expired_fulfilled_not_touched(reservation_service, item):
    """Fulfilled reservations are terminal — expiry should not re-cancel them."""
    res = reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u1", expires_at=_past()
        )
    )
    reservation_service.confirm_reservation(res.id)
    reservation_service.fulfill_reservation(res.id)
    fetched = reservation_service.get_reservation(res.id)
    assert fetched.status == ReservationStatus.FULFILLED


def test_get_expired_cancelled_not_touched(reservation_service, item_service, item):
    res = reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u1", expires_at=_past()
        )
    )
    reservation_service.cancel_reservation(res.id)
    # Second get should not double-decrement reserved_quantity
    fetched = reservation_service.get_reservation(res.id)
    assert fetched.status == ReservationStatus.CANCELLED
    avail = item_service.get_availability(item.id)
    assert avail.reserved_quantity == 0


# ── batch expire-stale ─────────────────────────────────────────────────────────

def test_expire_stale_cancels_expired_pending(reservation_service, item):
    reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u1", expires_at=_past()
        )
    )
    expired = reservation_service.expire_stale_reservations()
    assert len(expired) == 1
    assert expired[0].status == ReservationStatus.CANCELLED


def test_expire_stale_cancels_expired_confirmed(reservation_service, item):
    res = reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u1", expires_at=_past()
        )
    )
    reservation_service.confirm_reservation(res.id)
    expired = reservation_service.expire_stale_reservations()
    assert len(expired) == 1
    assert expired[0].status == ReservationStatus.CANCELLED


def test_expire_stale_releases_reserved_quantity(reservation_service, item_service, item):
    reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=20, requester_id="u1", expires_at=_past()
        )
    )
    reservation_service.expire_stale_reservations()
    avail = item_service.get_availability(item.id)
    assert avail.reserved_quantity == 0
    assert avail.available_quantity == 50


def test_expire_stale_skips_future_expiry(reservation_service, item):
    reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u1", expires_at=_future()
        )
    )
    expired = reservation_service.expire_stale_reservations()
    assert len(expired) == 0


def test_expire_stale_skips_no_expiry(reservation_service, item):
    reservation_service.create_reservation(
        CreateReservationRequest(item_id=item.id, quantity=5, requester_id="u1")
    )
    expired = reservation_service.expire_stale_reservations()
    assert len(expired) == 0


def test_expire_stale_skips_terminal_statuses(reservation_service, item):
    res = reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u1", expires_at=_past()
        )
    )
    reservation_service.cancel_reservation(res.id)
    expired = reservation_service.expire_stale_reservations()
    assert len(expired) == 0


def test_expire_stale_only_affects_expired_ones(reservation_service, item):
    reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u1", expires_at=_past()
        )
    )
    reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u2", expires_at=_future()
        )
    )
    reservation_service.create_reservation(
        CreateReservationRequest(item_id=item.id, quantity=5, requester_id="u3")
    )
    expired = reservation_service.expire_stale_reservations()
    assert len(expired) == 1

    active = reservation_service.list_reservations(status=ReservationStatus.PENDING)
    assert len(active) == 2


def test_expire_stale_idempotent(reservation_service, item):
    reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=item.id, quantity=5, requester_id="u1", expires_at=_past()
        )
    )
    reservation_service.expire_stale_reservations()
    second_run = reservation_service.expire_stale_reservations()
    assert len(second_run) == 0


# ── route tests ────────────────────────────────────────────────────────────────

def test_route_get_expired_reservation_returns_cancelled(client, item_service):
    item = client.post(
        "/items", json={"name": "Widget", "sku": "WGT-EXP", "total_quantity": 50}
    ).json()
    res = client.post(
        "/reservations",
        json={
            "item_id": item["id"],
            "quantity": 10,
            "requester_id": "u1",
            "expires_at": _past().isoformat(),
        },
    ).json()
    fetched = client.get(f"/reservations/{res['id']}").json()
    assert fetched["status"] == "CANCELLED"


def test_route_expire_stale_200(client):
    item = client.post(
        "/items", json={"name": "Widget", "sku": "WGT-STALE", "total_quantity": 50}
    ).json()
    client.post(
        "/reservations",
        json={
            "item_id": item["id"],
            "quantity": 5,
            "requester_id": "u1",
            "expires_at": _past().isoformat(),
        },
    )
    resp = client.post("/reservations/expire-stale")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["status"] == "CANCELLED"


def test_route_expire_stale_empty_when_none_expired(client):
    resp = client.post("/reservations/expire-stale")
    assert resp.status_code == 200
    assert resp.json() == []


def test_route_expire_stale_restores_availability(client):
    item = client.post(
        "/items", json={"name": "Widget", "sku": "WGT-AVAIL", "total_quantity": 20}
    ).json()
    client.post(
        "/reservations",
        json={
            "item_id": item["id"],
            "quantity": 20,
            "requester_id": "u1",
            "expires_at": _past().isoformat(),
        },
    )
    client.post("/reservations/expire-stale")
    avail = client.get(f"/items/{item['id']}/availability").json()
    assert avail["reserved_quantity"] == 0
    assert avail["available_quantity"] == 20
