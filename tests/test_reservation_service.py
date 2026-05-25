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
    ReservationNotFoundError,
    ReservationService,
)


@pytest.fixture
def item_repo():
    return InMemoryItemRepository()


@pytest.fixture
def reservation_repo():
    return InMemoryReservationRepository()


@pytest.fixture
def item_service(item_repo):
    return ItemService(repository=item_repo)


@pytest.fixture
def reservation_service(reservation_repo, item_service):
    return ReservationService(repository=reservation_repo, item_service=item_service)


@pytest.fixture
def existing_item(item_service):
    return item_service.create_item(
        CreateItemRequest(name="Widget", sku="WGT-001", total_quantity=50)
    )


def test_create_reservation_returns_reservation(reservation_service, existing_item):
    req = CreateReservationRequest(
        item_id=existing_item.id,
        quantity=10,
        requester_id="user-1",
    )
    reservation = reservation_service.create_reservation(req)

    assert reservation.id is not None
    assert reservation.item_id == existing_item.id
    assert reservation.quantity == 10
    assert reservation.status == ReservationStatus.PENDING
    assert reservation.requester_id == "user-1"
    assert reservation.created_at is not None


def test_create_reservation_decrements_available_quantity(
    reservation_service, item_service, existing_item
):
    req = CreateReservationRequest(
        item_id=existing_item.id, quantity=10, requester_id="user-1"
    )
    reservation_service.create_reservation(req)

    availability = item_service.get_availability(existing_item.id)
    assert availability.reserved_quantity == 10
    assert availability.available_quantity == 40


def test_create_reservation_insufficient_quantity_raises(
    reservation_service, existing_item
):
    req = CreateReservationRequest(
        item_id=existing_item.id, quantity=999, requester_id="user-1"
    )
    with pytest.raises(InsufficientQuantityError):
        reservation_service.create_reservation(req)


def test_create_reservation_exact_available_quantity_succeeds(
    reservation_service, existing_item
):
    req = CreateReservationRequest(
        item_id=existing_item.id, quantity=50, requester_id="user-1"
    )
    reservation = reservation_service.create_reservation(req)
    assert reservation.quantity == 50


def test_create_reservation_item_not_found_raises(reservation_service):
    from uuid import uuid4

    req = CreateReservationRequest(
        item_id=uuid4(), quantity=1, requester_id="user-1"
    )
    from app.services.item_service import ItemNotFoundError

    with pytest.raises(ItemNotFoundError):
        reservation_service.create_reservation(req)


def test_create_reservation_zero_quantity_raises(reservation_service, existing_item):
    with pytest.raises(Exception):
        CreateReservationRequest(
            item_id=existing_item.id, quantity=0, requester_id="user-1"
        )


def test_get_reservation_returns_existing(reservation_service, existing_item):
    req = CreateReservationRequest(
        item_id=existing_item.id, quantity=5, requester_id="user-1"
    )
    created = reservation_service.create_reservation(req)
    fetched = reservation_service.get_reservation(created.id)

    assert fetched.id == created.id
    assert fetched.quantity == 5


def test_get_reservation_not_found_raises(reservation_service):
    from uuid import uuid4

    with pytest.raises(ReservationNotFoundError):
        reservation_service.get_reservation(uuid4())


def test_list_reservations_empty(reservation_service):
    assert reservation_service.list_reservations() == []


def test_list_reservations_returns_all(reservation_service, existing_item):
    for i in range(3):
        reservation_service.create_reservation(
            CreateReservationRequest(
                item_id=existing_item.id, quantity=1, requester_id=f"user-{i}"
            )
        )
    results = reservation_service.list_reservations()
    assert len(results) == 3


def test_list_reservations_filter_by_item_id(reservation_service, item_service):
    item_a = item_service.create_item(
        CreateItemRequest(name="A", sku="A-001", total_quantity=10)
    )
    item_b = item_service.create_item(
        CreateItemRequest(name="B", sku="B-001", total_quantity=10)
    )
    reservation_service.create_reservation(
        CreateReservationRequest(item_id=item_a.id, quantity=1, requester_id="u1")
    )
    reservation_service.create_reservation(
        CreateReservationRequest(item_id=item_b.id, quantity=1, requester_id="u2")
    )

    results = reservation_service.list_reservations(item_id=item_a.id)
    assert len(results) == 1
    assert results[0].item_id == item_a.id


def test_list_reservations_filter_by_status(reservation_service, existing_item):
    reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=existing_item.id, quantity=1, requester_id="u1"
        )
    )
    results = reservation_service.list_reservations(status=ReservationStatus.PENDING)
    assert len(results) == 1

    results = reservation_service.list_reservations(status=ReservationStatus.CONFIRMED)
    assert len(results) == 0


def test_list_reservations_filter_by_requester_id(reservation_service, existing_item):
    reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=existing_item.id, quantity=1, requester_id="alice"
        )
    )
    reservation_service.create_reservation(
        CreateReservationRequest(
            item_id=existing_item.id, quantity=1, requester_id="bob"
        )
    )

    results = reservation_service.list_reservations(requester_id="alice")
    assert len(results) == 1
    assert results[0].requester_id == "alice"


def test_list_reservations_pagination(reservation_service, existing_item):
    for i in range(5):
        reservation_service.create_reservation(
            CreateReservationRequest(
                item_id=existing_item.id, quantity=1, requester_id=f"user-{i}"
            )
        )
    page = reservation_service.list_reservations(skip=2, limit=2)
    assert len(page) == 2
