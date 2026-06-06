from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_roles
from app.db.session import get_db
from app.domain.models import InventoryBalance, Item, Purchase, StockAlert, Unit, WasteItem, WasteRecord
from app.domain.enums import UserRole
from app.schemas.dashboard import GeneralDashboardResponse, LowStockItem, OwnerDashboardResponse

router = APIRouter()


async def _build_dashboard(db: AsyncSession) -> OwnerDashboardResponse:
    today = date.today()
    total_sku = await db.scalar(select(func.count(Item.id)).where(Item.is_active.is_(True)))
    inventory_value = await db.scalar(
        select(
            func.coalesce(
                func.sum(InventoryBalance.current_quantity * InventoryBalance.average_cost), 0
            )
        )
    )
    monthly_purchase_expense = await db.scalar(
        select(func.coalesce(func.sum(Purchase.total_amount), 0)).where(
            extract("year", Purchase.purchase_date) == today.year,
            extract("month", Purchase.purchase_date) == today.month,
        )
    )
    yearly_purchase_expense = await db.scalar(
        select(func.coalesce(func.sum(Purchase.total_amount), 0)).where(
            extract("year", Purchase.purchase_date) == today.year
        )
    )
    monthly_waste_value = await db.scalar(
        select(func.coalesce(func.sum(WasteItem.estimated_cost), 0))
        .join(WasteRecord, WasteRecord.id == WasteItem.waste_id)
        .where(
            extract("year", WasteRecord.waste_date) == today.year,
            extract("month", WasteRecord.waste_date) == today.month,
        )
    )

    low_stock_rows = (
        await db.execute(
            select(Item, Unit, InventoryBalance)
            .join(Unit, Unit.id == Item.unit_id)
            .join(InventoryBalance, InventoryBalance.item_id == Item.id)
            .where(Item.is_active.is_(True), InventoryBalance.current_quantity <= Item.minimum_stock)
            .order_by(InventoryBalance.current_quantity.asc())
            .limit(10)
        )
    ).all()
    low_stock_count = await db.scalar(
        select(func.count(Item.id))
        .join(InventoryBalance, InventoryBalance.item_id == Item.id)
        .where(Item.is_active.is_(True), InventoryBalance.current_quantity <= Item.minimum_stock)
    )
    low_stock_items = [
        LowStockItem(
            item_id=item.id,
            sku=item.sku,
            name=item.name,
            current_quantity=balance.current_quantity,
            minimum_stock=item.minimum_stock,
            unit_symbol=unit.symbol,
        )
        for item, unit, balance in low_stock_rows
    ]
    return OwnerDashboardResponse(
        total_sku=total_sku or 0,
        inventory_value=inventory_value or Decimal("0"),
        monthly_purchase_expense=monthly_purchase_expense or Decimal("0"),
        yearly_purchase_expense=yearly_purchase_expense or Decimal("0"),
        monthly_waste_value=monthly_waste_value or Decimal("0"),
        low_stock_count=low_stock_count or 0,
        low_stock_items=low_stock_items,
    )


@router.get(
    "",
    response_model=GeneralDashboardResponse,
    summary="Dashboard umum sesuai role",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def dashboard(db: AsyncSession = Depends(get_db)) -> GeneralDashboardResponse:
    base = await _build_dashboard(db)
    active_alerts = await db.scalar(select(func.count(StockAlert.id)).where(StockAlert.is_active.is_(True)))
    return GeneralDashboardResponse(**base.model_dump(), active_alerts=active_alerts or 0)


@router.get(
    "/owner",
    response_model=OwnerDashboardResponse,
    summary="Dashboard owner dengan KPI inventory dan biaya",
    dependencies=[Depends(require_roles(UserRole.OWNER))],
)
async def owner_dashboard(db: AsyncSession = Depends(get_db)) -> OwnerDashboardResponse:
    return await _build_dashboard(db)
