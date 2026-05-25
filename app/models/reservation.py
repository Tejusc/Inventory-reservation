from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.enums import ReservationStatus


class Reservation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    item_id: UUID
    quantity: int = Field(ge=1)
    status: ReservationStatus = ReservationStatus.PENDING
    requester_id: str
    notes: str | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateReservationRequest(BaseModel):
    item_id: UUID
    quantity: int = Field(ge=1)
    requester_id: str
    notes: str | None = None
    expires_at: datetime | None = None


class ReservationResponse(BaseModel):
    id: UUID
    item_id: UUID
    quantity: int
    status: ReservationStatus
    requester_id: str
    notes: str | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
