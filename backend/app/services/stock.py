from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.domain.enums import AlertType, MovementType
from app.domain.models import InventoryBalance, Item, StockAlert, StockMovement


ZERO = Decimal("0")


async def get_or_create_balance(db: AsyncSession, item_id: UUID) -> InventoryBalance:
    result = await db.execute(
        select(InventoryBalance).where(InventoryBalance.item_id == item_id).with_for_update()
    )
    balance = result.scalar_one_or_none()
    if balance:
        return balance

    item = await db.get(Item, item_id)
    if not item or not item.is_active:
        raise AppError("Barang tidak ditemukan atau nonaktif", status_code=status.HTTP_404_NOT_FOUND)

    balance = InventoryBalance(item_id=item_id, current_quantity=ZERO, average_cost=item.default_cost)
    db.add(balance)
    await db.flush()
    return balance


async def sync_stock_alerts(db: AsyncSession, item_id: UUID, balance: InventoryBalance) -> None:
    item = await db.get(Item, item_id)
    if not item:
        return

    now = datetime.now(timezone.utc)
    active_alerts = (
        await db.execute(
            select(StockAlert).where(StockAlert.item_id == item_id, StockAlert.is_active.is_(True))
        )
    ).scalars().all()

    desired_type: AlertType | None = None
    threshold = item.minimum_stock
    if balance.current_quantity <= ZERO:
        desired_type = AlertType.OUT_OF_STOCK
        threshold = ZERO
    elif balance.current_quantity <= item.minimum_stock:
        desired_type = AlertType.LOW_STOCK

    if desired_type is None:
        for alert in active_alerts:
            alert.is_active = False
            alert.resolved_at = now
            db.add(alert)
        return

    has_desired = False
    for alert in active_alerts:
        if alert.alert_type == desired_type:
            has_desired = True
            alert.current_quantity = balance.current_quantity
            alert.threshold_quantity = threshold
            db.add(alert)
        else:
            alert.is_active = False
            alert.resolved_at = now
            db.add(alert)

    if not has_desired:
        db.add(
            StockAlert(
                item_id=item_id,
                alert_type=desired_type,
                threshold_quantity=threshold,
                current_quantity=balance.current_quantity,
                is_active=True,
            )
        )


async def create_stock_movement(
    db: AsyncSession,
    *,
    item_id: UUID,
    movement_type: MovementType,
    quantity_change: Decimal,
    unit_cost: Decimal | None,
    reference_type: str | None,
    reference_id: UUID | None,
    note: str | None,
    performed_by_id: UUID,
) -> StockMovement:
    if quantity_change == ZERO:
        raise AppError("Perubahan stok tidak boleh 0")

    balance = await get_or_create_balance(db, item_id)
    old_qty = balance.current_quantity or ZERO
    old_avg = balance.average_cost or ZERO

    if quantity_change < ZERO:
        requested = abs(quantity_change)
        if old_qty < requested:
            raise AppError(
                "Stok tidak mencukupi untuk transaksi ini",
                status_code=status.HTTP_409_CONFLICT,
                code="insufficient_stock",
            )
        effective_unit_cost = old_avg
        balance.current_quantity = old_qty + quantity_change
    else:
        effective_unit_cost = unit_cost if unit_cost is not None else old_avg
        new_qty = old_qty + quantity_change
        total_value = (old_qty * old_avg) + (quantity_change * effective_unit_cost)
        balance.current_quantity = new_qty
        balance.average_cost = total_value / new_qty if new_qty > ZERO else effective_unit_cost

    balance.last_movement_at = datetime.now(timezone.utc)
    db.add(balance)

    movement = StockMovement(
        item_id=item_id,
        movement_type=movement_type,
        quantity_change=quantity_change,
        unit_cost=effective_unit_cost,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
        performed_by_id=performed_by_id,
    )
    db.add(movement)
    await db.flush()
    await sync_stock_alerts(db, item_id, balance)
    await db.flush()
    return movement

