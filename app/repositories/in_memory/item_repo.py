from __future__ import annotations

from uuid import UUID

from app.models.item import Item
from app.repositories.item_repository import ItemRepository


class InMemoryItemRepository(ItemRepository):

    def __init__(self) -> None:
        self._store: dict[UUID, Item] = {}

    def save(self, item: Item) -> Item:
        self._store[item.id] = item
        return item

    def find_by_id(self, item_id: UUID) -> Item | None:
        return self._store.get(item_id)

    def find_by_sku(self, sku: str) -> Item | None:
        return next((i for i in self._store.values() if i.sku == sku), None)

    def find_all(self, skip: int = 0, limit: int = 100) -> list[Item]:
        items = list(self._store.values())
        return items[skip: skip + limit]

    def delete(self, item_id: UUID) -> bool:
        if item_id in self._store:
            del self._store[item_id]
            return True
        return False
