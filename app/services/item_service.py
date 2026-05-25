from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.models.item import (
    AvailabilityResponse,
    CreateItemRequest,
    Item,
    ItemResponse,
    UpdateItemRequest,
)
from app.repositories.item_repository import ItemRepository


class ItemNotFoundError(Exception):
    pass


class DuplicateSKUError(Exception):
    pass


class ItemService:

    def __init__(self, repository: ItemRepository) -> None:
        self._repo = repository

    def create_item(self, req: CreateItemRequest) -> ItemResponse:
        if self._repo.find_by_sku(req.sku) is not None:
            raise DuplicateSKUError(f"SKU '{req.sku}' already exists")

        item = Item(
            name=req.name,
            description=req.description,
            sku=req.sku,
            total_quantity=req.total_quantity,
        )
        saved = self._repo.save(item)
        return ItemResponse.model_validate(saved.model_dump())

    def get_item(self, item_id: UUID) -> ItemResponse:
        item = self._repo.find_by_id(item_id)
        if item is None:
            raise ItemNotFoundError(f"Item '{item_id}' not found")
        return ItemResponse.model_validate(item.model_dump())

    def list_items(self, skip: int = 0, limit: int = 100) -> list[ItemResponse]:
        items = self._repo.find_all(skip=skip, limit=limit)
        return [ItemResponse.model_validate(i.model_dump()) for i in items]

    def update_item(self, item_id: UUID, req: UpdateItemRequest) -> ItemResponse:
        item = self._repo.find_by_id(item_id)
        if item is None:
            raise ItemNotFoundError(f"Item '{item_id}' not found")

        updated = item.model_copy(
            update={
                k: v
                for k, v in req.model_dump(exclude_none=True).items()
            }
            | {"updated_at": datetime.now(timezone.utc)}
        )
        saved = self._repo.save(updated)
        return ItemResponse.model_validate(saved.model_dump())

    def delete_item(self, item_id: UUID) -> None:
        removed = self._repo.delete(item_id)
        if not removed:
            raise ItemNotFoundError(f"Item '{item_id}' not found")

    def get_availability(self, item_id: UUID) -> AvailabilityResponse:
        item = self._repo.find_by_id(item_id)
        if item is None:
            raise ItemNotFoundError(f"Item '{item_id}' not found")
        return AvailabilityResponse(
            item_id=item.id,
            total_quantity=item.total_quantity,
            reserved_quantity=item.reserved_quantity,
            available_quantity=item.available_quantity,
        )

    # Called by reservation service — keeps reserved_quantity consistent
    def adjust_reserved_quantity(self, item_id: UUID, delta: int) -> None:
        item = self._repo.find_by_id(item_id)
        if item is None:
            raise ItemNotFoundError(f"Item '{item_id}' not found")
        updated = item.model_copy(
            update={
                "reserved_quantity": item.reserved_quantity + delta,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._repo.save(updated)
