from __future__ import annotations

import pytest

from app.models.enums import ReservationStatus
from app.models.item import CreateItemRequest
from app.models.reservation import CreateReservationRequest
from app.repositories.in_memory.item_repo import InMemoryItemRepository
from app.repositories.in_memory.reservation_repo import InMemoryReservationRepository
from app.services.item_service import ItemService
from app.services.reservation_service import (
    InsufficientQuantityError,
    InvalidTransitionError,
    ReservationService,
)


@pytest.fixture
def item_repo():
    return InMemoryItemRepository()


@pytest.fixture
def item_service(item_repo):
    return ItemService(repository=item_repo)


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


@pytest.fixture
def pending_reservation(reservation_service, item):
    return reservation_service.create_reservation(
        CreateReservationRequest(item_id=item.id, quantity=10, requester_id="user-1")
    )


# ── confirm ────────────────────────────────────────────────────────────────────

def test_confirm_pending_sets_confirmed(reservation_service, pending_reservation):
    result = reservation_service.confirm_reservation(pending_reservation.id)
    assert result.status == ReservationStatus.CONFIRMED


def test_confirm_does_not_change_reserved_quantity(
    reservation_service, item_service, item, pending_reservation
):
    reservation_service.confirm_reservation(pending_reservation.id)
    avail = item_service.get_availability(item.id)
    assert avail.reserved_quantity == 10


def test_confirm_confirmed_raises_invalid_transition(
    reservation_service, pending_reservation
):
    reservation_service.confirm_reservation(pending_reservation.id)
    with pytest.raises(InvalidTransitionError):
        reservation_service.confirm_reservation(pending_reservation.id)


def test_confirm_cancelled_raises_invalid_transition(
    reservation_service, pending_reservation
):
    reservation_service.cancel_reservation(pending_reservation.id)
    with pytest.raises(InvalidTransitionError):
        reservation_service.confirm_reservation(pending_reservation.id)


def test_confirm_fulfilled_raises_invalid_transition(
    reservation_service, pending_reservation
):
    reservation_service.confirm_reservation(pending_reservation.id)
    reservation_service.fulfill_reservation(pending_reservation.id)
    with pytest.raises(InvalidTransitionError):
        reservation_service.confirm_reservation(pending_reservation.id)


# ── cancel ─────────────────────────────────────────────────────────────────────

def test_cancel_pending_sets_cancelled(reservation_service, pending_reservation):
    result = reservation_service.cancel_reservation(pending_reservation.id)
    assert result.status == ReservationStatus.CANCELLED


def test_cancel_pending_decrements_reserved_quantity(
    reservation_service, item_service, item, pending_reservation
):
    reservation_service.cancel_reservation(pending_reservation.id)
    avail = item_service.get_availability(item.id)
    assert avail.reserved_quantity == 0
    assert avail.available_quantity == 50


def test_cancel_confirmed_sets_cancelled(reservation_service, pending_reservation):
    reservation_service.confirm_reservation(pending_reservation.id)
    result = reservation_service.cancel_reservation(pending_reservation.id)
    assert result.status == ReservationStatus.CANCELLED


def test_cancel_confirmed_decrements_reserved_quantity(
    reservation_service, item_service, item, pending_reservation
):
    reservation_service.confirm_reservation(pending_reservation.id)
    reservation_service.cancel_reservation(pending_reservation.id)
    avail = item_service.get_availability(item.id)
    assert avail.reserved_quantity == 0
    assert avail.available_quantity == 50


def test_cancel_already_cancelled_raises_invalid_transition(
    reservation_service, pending_reservation
):
    reservation_service.cancel_reservation(pending_reservation.id)
    with pytest.raises(InvalidTransitionError):
        reservation_service.cancel_reservation(pending_reservation.id)


def test_cancel_fulfilled_raises_invalid_transition(
    reservation_service, pending_reservation
):
    reservation_service.confirm_reservation(pending_reservation.id)
    reservation_service.fulfill_reservation(pending_reservation.id)
    with pytest.raises(InvalidTransitionError):
        reservation_service.cancel_reservation(pending_reservation.id)


# ── fulfill ────────────────────────────────────────────────────────────────────

def test_fulfill_confirmed_sets_fulfilled(reservation_service, pending_reservation):
    reservation_service.confirm_reservation(pending_reservation.id)
    result = reservation_service.fulfill_reservation(pending_reservation.id)
    assert result.status == ReservationStatus.FULFILLED


def test_fulfill_decrements_reserved_quantity(
    reservation_service, item_service, item, pending_reservation
):
    reservation_service.confirm_reservation(pending_reservation.id)
    reservation_service.fulfill_reservation(pending_reservation.id)
    avail = item_service.get_availability(item.id)
    assert avail.reserved_quantity == 0


def test_fulfill_also_decrements_total_quantity(
    reservation_service, item_service, item, pending_reservation
):
    reservation_service.confirm_reservation(pending_reservation.id)
    reservation_service.fulfill_reservation(pending_reservation.id)
    avail = item_service.get_availability(item.id)
    assert avail.total_quantity == 40
    assert avail.available_quantity == 40


def test_fulfill_pending_raises_invalid_transition(
    reservation_service, pending_reservation
):
    with pytest.raises(InvalidTransitionError):
        reservation_service.fulfill_reservation(pending_reservation.id)


def test_fulfill_already_fulfilled_raises_invalid_transition(
    reservation_service, pending_reservation
):
    reservation_service.confirm_reservation(pending_reservation.id)
    reservation_service.fulfill_reservation(pending_reservation.id)
    with pytest.raises(InvalidTransitionError):
        reservation_service.fulfill_reservation(pending_reservation.id)


def test_fulfill_cancelled_raises_invalid_transition(
    reservation_service, pending_reservation
):
    reservation_service.cancel_reservation(pending_reservation.id)
    with pytest.raises(InvalidTransitionError):
        reservation_service.fulfill_reservation(pending_reservation.id)


# ── concurrency guard ──────────────────────────────────────────────────────────

def test_concurrent_reservations_cannot_exceed_stock(item_service):
    """Two threads race to reserve the last 5 units — only one should succeed."""
    import threading

    item = item_service.create_item(
        CreateItemRequest(name="Limited", sku="LTD-001", total_quantity=5)
    )
    svc = ReservationService(
        repository=InMemoryReservationRepository(),
        item_service=item_service,
    )
    results = []

    def attempt():
        try:
            svc.create_reservation(
                CreateReservationRequest(item_id=item.id, quantity=5, requester_id="racer")
            )
            results.append("ok")
        except InsufficientQuantityError:
            results.append("rejected")

    threads = [threading.Thread(target=attempt) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count("ok") == 1
    assert results.count("rejected") == 4
    avail = item_service.get_availability(item.id)
    assert avail.reserved_quantity == 5
    assert avail.available_quantity == 0
