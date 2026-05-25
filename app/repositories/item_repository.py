from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.models.item import Item


class ItemRepository(ABC):

    @abstractmethod
    def save(self, item: Item) -> Item:
        ...

    @abstractmethod
    def find_by_id(self, item_id: UUID) -> Item | None:
        ...

    @abstractmethod
    def find_by_sku(self, sku: str) -> Item | None:
        ...

    @abstractmethod
    def find_all(self, skip: int = 0, limit: int = 100) -> list[Item]:
        ...

    @abstractmethod
    def delete(self, item_id: UUID) -> bool:
        ...
