from __future__ import annotations

from uuid import UUID

from app.models.enums import ReservationStatus
from app.models.reservation import Reservation
from app.repositories.reservation_repository import ReservationRepository


class InMemoryReservationRepository(ReservationRepository):

    def __init__(self) -> None:
        self._store: dict[UUID, Reservation] = {}

    def save(self, reservation: Reservation) -> Reservation:
        self._store[reservation.id] = reservation
        return reservation

    def find_by_id(self, reservation_id: UUID) -> Reservation | None:
        return self._store.get(reservation_id)

    def find_all(
        self,
        item_id: UUID | None = None,
        status: ReservationStatus | None = None,
        requester_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Reservation]:
        results = list(self._store.values())
        if item_id is not None:
            results = [r for r in results if r.item_id == item_id]
        if status is not None:
            results = [r for r in results if r.status == status]
        if requester_id is not None:
            results = [r for r in results if r.requester_id == requester_id]
        return results[skip: skip + limit]
