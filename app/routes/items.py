from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.dependencies import get_item_service
from app.models.item import AvailabilityResponse, CreateItemRequest, ItemResponse, UpdateItemRequest
from app.services.item_service import DuplicateSKUError, ItemNotFoundError, ItemService

router = APIRouter()


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    req: CreateItemRequest,
    service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    try:
        return service.create_item(req)
    except DuplicateSKUError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("", response_model=list[ItemResponse])
def list_items(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    service: ItemService = Depends(get_item_service),
) -> list[ItemResponse]:
    return service.list_items(skip=skip, limit=limit)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: UUID,
    service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    try:
        return service.get_item(item_id)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: UUID,
    req: UpdateItemRequest,
    service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    try:
        return service.update_item(item_id, req)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_item(
    item_id: UUID,
    service: ItemService = Depends(get_item_service),
) -> Response:
    try:
        service.delete_item(item_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{item_id}/availability", response_model=AvailabilityResponse)
def get_availability(
    item_id: UUID,
    service: ItemService = Depends(get_item_service),
) -> AvailabilityResponse:
    try:
        return service.get_availability(item_id)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
