from __future__ import annotations

import threading
from datetime import datetime, timezone
from uuid import UUID

from app.models.enums import ReservationStatus
from app.models.reservation import CreateReservationRequest, Reservation, ReservationResponse
from app.repositories.reservation_repository import ReservationRepository
from app.services.item_service import ItemService


class ReservationNotFoundError(Exception):
    pass


class InsufficientQuantityError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


# Maps each status to the set of statuses it may transition into.
_ALLOWED_TRANSITIONS: dict[ReservationStatus, set[ReservationStatus]] = {
    ReservationStatus.PENDING: {ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED},
    ReservationStatus.CONFIRMED: {ReservationStatus.FULFILLED, ReservationStatus.CANCELLED},
    ReservationStatus.FULFILLED: set(),
    ReservationStatus.CANCELLED: set(),
}


class ReservationService:

    def __init__(self, repository: ReservationRepository, item_service: ItemService) -> None:
        self._repo = repository
        self._item_service = item_service
        self._lock = threading.Lock()

    # ── create ──────────────────────────────────────────────────────────────

    def create_reservation(self, req: CreateReservationRequest) -> ReservationResponse:
        with self._lock:
            availability = self._item_service.get_availability(req.item_id)

            if availability.available_quantity < req.quantity:
                raise InsufficientQuantityError(
                    f"Requested {req.quantity} but only "
                    f"{availability.available_quantity} available"
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

    # ── read ─────────────────────────────────────────────────────────────────

    def get_reservation(self, reservation_id: UUID) -> ReservationResponse:
        reservation = self._repo.find_by_id(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(f"Reservation '{reservation_id}' not found")
        now = datetime.now(timezone.utc)
        if self._is_expired(reservation, now):
            return self._do_cancel(reservation)
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

    # ── lifecycle ────────────────────────────────────────────────────────────

    def confirm_reservation(self, reservation_id: UUID) -> ReservationResponse:
        return self._transition(reservation_id, ReservationStatus.CONFIRMED)

    def cancel_reservation(self, reservation_id: UUID) -> ReservationResponse:
        reservation = self._repo.find_by_id(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(f"Reservation '{reservation_id}' not found")

        self._assert_transition_allowed(reservation.status, ReservationStatus.CANCELLED)

        with self._lock:
            self._item_service.adjust_reserved_quantity(
                reservation.item_id, delta=-reservation.quantity
            )
            return self._save_status(reservation, ReservationStatus.CANCELLED)

    def fulfill_reservation(self, reservation_id: UUID) -> ReservationResponse:
        reservation = self._repo.find_by_id(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(f"Reservation '{reservation_id}' not found")

        self._assert_transition_allowed(reservation.status, ReservationStatus.FULFILLED)

        with self._lock:
            self._item_service.consume_quantity(reservation.item_id, reservation.quantity)
            return self._save_status(reservation, ReservationStatus.FULFILLED)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _transition(self, reservation_id: UUID, target: ReservationStatus) -> ReservationResponse:
        reservation = self._repo.find_by_id(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(f"Reservation '{reservation_id}' not found")
        self._assert_transition_allowed(reservation.status, target)
        return self._save_status(reservation, target)

    @staticmethod
    def _assert_transition_allowed(
        current: ReservationStatus, target: ReservationStatus
    ) -> None:
        if target not in _ALLOWED_TRANSITIONS[current]:
            raise InvalidTransitionError(
                f"Cannot transition from {current.value} to {target.value}"
            )

    def _save_status(
        self, reservation: Reservation, target: ReservationStatus
    ) -> ReservationResponse:
        updated = reservation.model_copy(
            update={"status": target, "updated_at": datetime.now(timezone.utc)}
        )
        self._repo.save(updated)
        return ReservationResponse.model_validate(updated.model_dump())

    # ── expiry ───────────────────────────────────────────────────────────────

    def expire_stale_reservations(self) -> list[ReservationResponse]:
        """Cancel all PENDING/CONFIRMED reservations past their expires_at."""
        now = datetime.now(timezone.utc)
        stale = self._repo.find_expired(before=now)
        return [self._do_cancel(r) for r in stale]

    @staticmethod
    def _is_expired(reservation: Reservation, now: datetime) -> bool:
        return (
            reservation.expires_at is not None
            and reservation.expires_at < now
            and reservation.status in {ReservationStatus.PENDING, ReservationStatus.CONFIRMED}
        )

    def _do_cancel(self, reservation: Reservation) -> ReservationResponse:
        with self._lock:
            self._item_service.adjust_reserved_quantity(
                reservation.item_id, delta=-reservation.quantity
            )
            return self._save_status(reservation, ReservationStatus.CANCELLED)
