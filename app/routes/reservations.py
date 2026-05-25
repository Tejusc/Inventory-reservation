from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.enums import ReservationStatus
from app.models.reservation import CreateReservationRequest, ReservationResponse
from app.repositories.in_memory.item_repo import InMemoryItemRepository
from app.repositories.in_memory.reservation_repo import InMemoryReservationRepository
from app.services.item_service import ItemNotFoundError, ItemService
from app.services.reservation_service import (
    InsufficientQuantityError,
    InvalidTransitionError,
    ReservationNotFoundError,
    ReservationService,
)

router = APIRouter()

_item_repo = InMemoryItemRepository()
_item_service = ItemService(repository=_item_repo)
_reservation_repo = InMemoryReservationRepository()
_default_service = ReservationService(repository=_reservation_repo, item_service=_item_service)


def get_reservation_service() -> ReservationService:
    return _default_service


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    req: CreateReservationRequest,
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponse:
    try:
        return service.create_reservation(req)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InsufficientQuantityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("", response_model=list[ReservationResponse])
def list_reservations(
    item_id: UUID | None = Query(default=None),
    status_filter: ReservationStatus | None = Query(default=None, alias="status"),
    requester_id: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    service: ReservationService = Depends(get_reservation_service),
) -> list[ReservationResponse]:
    return service.list_reservations(
        item_id=item_id,
        status=status_filter,
        requester_id=requester_id,
        skip=skip,
        limit=limit,
    )


@router.post("/expire-stale", response_model=list[ReservationResponse])
def expire_stale(
    service: ReservationService = Depends(get_reservation_service),
) -> list[ReservationResponse]:
    return service.expire_stale_reservations()


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(
    reservation_id: UUID,
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponse:
    try:
        return service.get_reservation(reservation_id)
    except ReservationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{reservation_id}/confirm", response_model=ReservationResponse)
def confirm_reservation(
    reservation_id: UUID,
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponse:
    try:
        return service.confirm_reservation(reservation_id)
    except ReservationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
def cancel_reservation(
    reservation_id: UUID,
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponse:
    try:
        return service.cancel_reservation(reservation_id)
    except ReservationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/{reservation_id}/fulfill", response_model=ReservationResponse)
def fulfill_reservation(
    reservation_id: UUID,
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponse:
    try:
        return service.fulfill_reservation(reservation_id)
    except ReservationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
