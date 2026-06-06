from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class LowStockItem(BaseModel):
    item_id: UUID
    sku: str
    name: str
    current_quantity: Decimal
    minimum_stock: Decimal
    unit_symbol: str


class OwnerDashboardResponse(BaseModel):
    total_sku: int
    inventory_value: Decimal
    monthly_purchase_expense: Decimal
    yearly_purchase_expense: Decimal
    monthly_waste_value: Decimal
    low_stock_count: int
    low_stock_items: list[LowStockItem]

class GeneralDashboardResponse(OwnerDashboardResponse):
    active_alerts: int

