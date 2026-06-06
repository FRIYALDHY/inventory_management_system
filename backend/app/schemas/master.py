from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import Timestamped


class SupplierBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    contact_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    address: str | None = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    contact_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    address: str | None = None
    is_active: bool | None = None


class SupplierResponse(Timestamped, SupplierBase):
    id: UUID


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None


class CategoryResponse(Timestamped):
    id: UUID
    name: str
    description: str | None


class UnitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    symbol: str = Field(min_length=1, max_length=20)


class UnitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    symbol: str | None = Field(default=None, min_length=1, max_length=20)


class UnitResponse(Timestamped):
    id: UUID
    name: str
    symbol: str


class ItemBase(BaseModel):
    sku: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    category_id: UUID | None = None
    unit_id: UUID
    minimum_stock: Decimal = Field(default=Decimal("0"), ge=0)
    reorder_level: Decimal = Field(default=Decimal("0"), ge=0)
    default_cost: Decimal = Field(default=Decimal("0"), ge=0)
    is_active: bool = True
    notes: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=2, max_length=80)
    name: str | None = Field(default=None, min_length=2, max_length=180)
    category_id: UUID | None = None
    unit_id: UUID | None = None
    minimum_stock: Decimal | None = Field(default=None, ge=0)
    reorder_level: Decimal | None = Field(default=None, ge=0)
    default_cost: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None
    notes: str | None = None


class ItemBalanceResponse(BaseModel):
    current_quantity: Decimal
    average_cost: Decimal
    last_movement_at: datetime | None


class ItemResponse(Timestamped):
    id: UUID
    sku: str
    name: str
    category_id: UUID | None
    unit_id: UUID
    minimum_stock: Decimal
    reorder_level: Decimal
    default_cost: Decimal
    is_active: bool
    notes: str | None
    category: CategoryResponse | None = None
    unit: UnitResponse
    balance: ItemBalanceResponse | None = None

