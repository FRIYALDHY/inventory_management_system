from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import PurchaseStatus
from app.schemas.common import Timestamped
from app.schemas.master import SupplierResponse
from app.schemas.users import UserResponse


class PurchaseItemCreate(BaseModel):
    item_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class PurchaseCreate(BaseModel):
    purchase_number: str = Field(min_length=2, max_length=80)
    supplier_id: UUID | None = None
    purchase_date: date
    notes: str | None = None
    items: list[PurchaseItemCreate] = Field(min_length=1)


class PurchaseUpdate(BaseModel):
    supplier_id: UUID | None = None
    purchase_date: date | None = None
    status: PurchaseStatus | None = None
    notes: str | None = None


class PurchaseItemResponse(Timestamped):
    id: UUID
    item_id: UUID
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal
    received_quantity: Decimal


class PurchaseResponse(Timestamped):
    id: UUID
    purchase_number: str
    supplier_id: UUID | None
    purchase_date: date
    status: PurchaseStatus
    total_amount: Decimal
    notes: str | None
    supplier: SupplierResponse | None = None
    created_by: UserResponse | None = None
    items: list[PurchaseItemResponse]


class PurchaseReceiveItem(BaseModel):
    purchase_item_id: UUID
    quantity: Decimal = Field(gt=0)


class PurchaseReceiveRequest(BaseModel):
    receipt_number: str = Field(min_length=2, max_length=80)
    receipt_date: date
    notes: str | None = None
    items: list[PurchaseReceiveItem] = Field(min_length=1)

    @model_validator(mode="after")
    def ensure_unique_purchase_items(self) -> "PurchaseReceiveRequest":
        ids = [item.purchase_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("purchase_item_id tidak boleh duplikat")
        return self

