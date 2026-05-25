from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.in_memory.item_repo import InMemoryItemRepository
from app.repositories.in_memory.reservation_repo import InMemoryReservationRepository
from app.services.item_service import ItemService
from app.services.reservation_service import ReservationService


@pytest.fixture
def item_repo() -> InMemoryItemRepository:
    return InMemoryItemRepository()


@pytest.fixture
def reservation_repo() -> InMemoryReservationRepository:
    return InMemoryReservationRepository()


@pytest.fixture
def item_service(item_repo: InMemoryItemRepository) -> ItemService:
    return ItemService(repository=item_repo)


@pytest.fixture
def reservation_service(
    reservation_repo: InMemoryReservationRepository,
    item_service: ItemService,
) -> ReservationService:
    return ReservationService(repository=reservation_repo, item_service=item_service)


@pytest.fixture
def client(item_service: ItemService, reservation_service: ReservationService) -> TestClient:
    app = create_app()

    import app.dependencies as deps

    app.dependency_overrides[deps.get_item_service] = lambda: item_service
    app.dependency_overrides[deps.get_reservation_service] = lambda: reservation_service

    return TestClient(app)
