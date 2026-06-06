from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import Timestamped


class WasteItemCreate(BaseModel):
    item_id: UUID
    quantity: Decimal = Field(gt=0)
    reason: str = Field(min_length=2, max_length=255)


class WasteCreate(BaseModel):
    waste_number: str = Field(min_length=2, max_length=80)
    waste_date: date
    notes: str | None = None
    items: list[WasteItemCreate] = Field(min_length=1)


class WasteItemResponse(Timestamped):
    id: UUID
    item_id: UUID
    quantity: Decimal
    reason: str
    unit_cost: Decimal
    estimated_cost: Decimal


class WasteResponse(Timestamped):
    id: UUID
    waste_number: str
    waste_date: date
    notes: str | None
    items: list[WasteItemResponse]

