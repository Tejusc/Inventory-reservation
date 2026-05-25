from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field


class Item(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    sku: str
    total_quantity: int = Field(ge=0)
    reserved_quantity: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @computed_field
    @property
    def available_quantity(self) -> int:
        return self.total_quantity - self.reserved_quantity


class CreateItemRequest(BaseModel):
    name: str
    description: str | None = None
    sku: str
    total_quantity: int = Field(ge=0)


class UpdateItemRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    total_quantity: int | None = Field(default=None, ge=0)


class ItemResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    sku: str
    total_quantity: int
    reserved_quantity: int
    available_quantity: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AvailabilityResponse(BaseModel):
    item_id: UUID
    total_quantity: int
    reserved_quantity: int
    available_quantity: int
