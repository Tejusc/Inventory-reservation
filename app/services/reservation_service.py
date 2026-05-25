from __future__ import annotations

from uuid import UUID

from app.models.enums import ReservationStatus
from app.models.reservation import CreateReservationRequest, Reservation, ReservationResponse
from app.repositories.reservation_repository import ReservationRepository
from app.services.item_service import ItemService


class ReservationNotFoundError(Exception):
    pass


class InsufficientQuantityError(Exception):
    pass


class ReservationService:

    def __init__(self, repository: ReservationRepository, item_service: ItemService) -> None:
        self._repo = repository
        self._item_service = item_service

    def create_reservation(self, req: CreateReservationRequest) -> ReservationResponse:
        availability = self._item_service.get_availability(req.item_id)

        if availability.available_quantity < req.quantity:
            raise InsufficientQuantityError(
                f"Requested {req.quantity} but only {availability.available_quantity} available"
            )

        reservation = Reservation(
            item_id=req.item_id,
            quantity=req.quantity,
            requester_id=req.requester_id,
            notes=req.notes,
            expires_at=req.expires_at,
        )
        self._repo.save(reservation)
        self._item_service.adjust_reserved_quantity(req.item_id, delta=req.quantity)

        return ReservationResponse.model_validate(reservation.model_dump())

    def get_reservation(self, reservation_id: UUID) -> ReservationResponse:
        reservation = self._repo.find_by_id(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(f"Reservation '{reservation_id}' not found")
        return ReservationResponse.model_validate(reservation.model_dump())

    def list_reservations(
        self,
        item_id: UUID | None = None,
        status: ReservationStatus | None = None,
        requester_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ReservationResponse]:
        reservations = self._repo.find_all(
            item_id=item_id,
            status=status,
            requester_id=requester_id,
            skip=skip,
            limit=limit,
        )
        return [ReservationResponse.model_validate(r.model_dump()) for r in reservations]
