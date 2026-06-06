from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import AlertType, MovementType
from app.schemas.common import Timestamped


class ReceiptItemCreate(BaseModel):
    item_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)


class InventoryReceiptCreate(BaseModel):
    receipt_number: str = Field(min_length=2, max_length=80)
    receipt_date: date
    notes: str | None = None
    items: list[ReceiptItemCreate] = Field(min_length=1)


class InventoryReceiptItemResponse(Timestamped):
    id: UUID
    item_id: UUID
    purchase_item_id: UUID | None
    quantity: Decimal
    unit_cost: Decimal


class InventoryReceiptResponse(Timestamped):
    id: UUID
    receipt_number: str
    purchase_id: UUID | None
    receipt_date: date
    notes: str | None
    items: list[InventoryReceiptItemResponse]


class IssueItemCreate(BaseModel):
    item_id: UUID
    quantity: Decimal = Field(gt=0)


class InventoryIssueCreate(BaseModel):
    issue_number: str = Field(min_length=2, max_length=80)
    issue_date: date
    destination: str | None = Field(default=None, max_length=150)
    notes: str | None = None
    items: list[IssueItemCreate] = Field(min_length=1)


class InventoryIssueItemResponse(Timestamped):
    id: UUID
    item_id: UUID
    quantity: Decimal
    unit_cost: Decimal


class InventoryIssueResponse(Timestamped):
    id: UUID
    issue_number: str
    issue_date: date
    destination: str | None
    notes: str | None
    items: list[InventoryIssueItemResponse]


class InventoryBalanceRow(BaseModel):
    item_id: UUID
    sku: str
    item_name: str
    unit_symbol: str
    current_quantity: Decimal
    minimum_stock: Decimal
    reorder_level: Decimal
    average_cost: Decimal
    inventory_value: Decimal
    last_movement_at: datetime | None
    is_low_stock: bool


class StockMovementResponse(Timestamped):
    id: UUID
    item_id: UUID
    movement_type: MovementType
    quantity_change: Decimal
    unit_cost: Decimal
    reference_type: str | None
    reference_id: UUID | None
    note: str | None
    performed_by_id: UUID


class StockAlertResponse(Timestamped):
    id: UUID
    item_id: UUID
    alert_type: AlertType
    threshold_quantity: Decimal
    current_quantity: Decimal
    is_active: bool
    resolved_at: datetime | None

