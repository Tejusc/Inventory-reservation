from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.models.enums import ReservationStatus
from app.models.reservation import Reservation


class ReservationRepository(ABC):

    @abstractmethod
    def save(self, reservation: Reservation) -> Reservation:
        ...

    @abstractmethod
    def find_by_id(self, reservation_id: UUID) -> Reservation | None:
        ...

    @abstractmethod
    def find_all(
        self,
        item_id: UUID | None = None,
        status: ReservationStatus | None = None,
        requester_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Reservation]:
        ...
