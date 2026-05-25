from __future__ import annotations

from app.repositories.in_memory.item_repo import InMemoryItemRepository
from app.repositories.in_memory.reservation_repo import InMemoryReservationRepository
from app.services.item_service import ItemService
from app.services.reservation_service import ReservationService

_item_repo = InMemoryItemRepository()
_item_service = ItemService(repository=_item_repo)

_reservation_repo = InMemoryReservationRepository()
_reservation_service = ReservationService(
    repository=_reservation_repo,
    item_service=_item_service,
)


def get_item_service() -> ItemService:
    return _item_service


def get_reservation_service() -> ReservationService:
    return _reservation_service
