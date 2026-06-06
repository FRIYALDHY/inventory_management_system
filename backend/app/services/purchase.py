from decimal import Decimal
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.domain.enums import MovementType, PurchaseStatus
from app.domain.models import (
    InventoryReceipt,
    InventoryReceiptItem,
    Item,
    Purchase,
    PurchaseItem,
    Supplier,
)
from app.schemas.purchase import PurchaseCreate, PurchaseReceiveRequest
from app.services.audit import write_audit_log
from app.services.stock import create_stock_movement


async def create_purchase(db: AsyncSession, payload: PurchaseCreate, actor_id: UUID) -> Purchase:
    if payload.supplier_id:
        supplier = await db.get(Supplier, payload.supplier_id)
        if not supplier or not supplier.is_active:
            raise AppError("Supplier tidak ditemukan atau nonaktif", status_code=status.HTTP_404_NOT_FOUND)

    item_ids = [item.item_id for item in payload.items]
    if len(item_ids) != len(set(item_ids)):
        raise AppError("Item pembelian tidak boleh duplikat")

    items = (await db.execute(select(Item).where(Item.id.in_(item_ids), Item.is_active.is_(True)))).scalars().all()
    if len(items) != len(item_ids):
        raise AppError("Satu atau lebih barang tidak ditemukan/nonaktif", status_code=status.HTTP_404_NOT_FOUND)

    purchase = Purchase(
        purchase_number=payload.purchase_number,
        supplier_id=payload.supplier_id,
        purchase_date=payload.purchase_date,
        notes=payload.notes,
        created_by_id=actor_id,
        status=PurchaseStatus.ORDERED,
    )
    total = Decimal("0")
    for item in payload.items:
        subtotal = item.quantity * item.unit_price
        total += subtotal
        purchase.items.append(
            PurchaseItem(
                item_id=item.item_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=subtotal,
            )
        )
    purchase.total_amount = total
    db.add(purchase)
    await db.flush()
    await write_audit_log(
        db,
        actor_id=actor_id,
        action="CREATE",
        entity_name="Purchase",
        entity_id=purchase.id,
        metadata={"purchase_number": purchase.purchase_number, "total_amount": str(total)},
    )
    return purchase


async def receive_purchase(
    db: AsyncSession,
    purchase_id: UUID,
    payload: PurchaseReceiveRequest,
    actor_id: UUID,
) -> InventoryReceipt:
    purchase = (
        await db.execute(
            select(Purchase)
            .where(Purchase.id == purchase_id)
            .options(selectinload(Purchase.items))
            .with_for_update()
        )
    ).scalar_one_or_none()
    if not purchase:
        raise AppError("Purchase tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    if purchase.status == PurchaseStatus.CANCELLED:
        raise AppError("Purchase yang dibatalkan tidak bisa diterima")

    by_id = {item.id: item for item in purchase.items}
    receipt = InventoryReceipt(
        receipt_number=payload.receipt_number,
        purchase_id=purchase.id,
        receipt_date=payload.receipt_date,
        notes=payload.notes,
        created_by_id=actor_id,
    )
    db.add(receipt)
    await db.flush()

    for received in payload.items:
        purchase_item = by_id.get(received.purchase_item_id)
        if not purchase_item:
            raise AppError("Item tidak termasuk purchase ini", status_code=status.HTTP_400_BAD_REQUEST)

        remaining = purchase_item.quantity - purchase_item.received_quantity
        if received.quantity > remaining:
            raise AppError(
                "Jumlah terima melebihi sisa purchase",
                status_code=status.HTTP_409_CONFLICT,
                code="receive_exceeds_remaining",
            )

        purchase_item.received_quantity += received.quantity
        receipt_item = InventoryReceiptItem(
            receipt_id=receipt.id,
            item_id=purchase_item.item_id,
            purchase_item_id=purchase_item.id,
            quantity=received.quantity,
            unit_cost=purchase_item.unit_price,
        )
        db.add(receipt_item)
        await create_stock_movement(
            db,
            item_id=purchase_item.item_id,
            movement_type=MovementType.PURCHASE_IN,
            quantity_change=received.quantity,
            unit_cost=purchase_item.unit_price,
            reference_type="InventoryReceipt",
            reference_id=receipt.id,
            note=f"Receive purchase {purchase.purchase_number}",
            performed_by_id=actor_id,
        )

    all_received = all(item.received_quantity >= item.quantity for item in purchase.items)
    any_received = any(item.received_quantity > 0 for item in purchase.items)
    purchase.status = PurchaseStatus.RECEIVED if all_received else (
        PurchaseStatus.PARTIALLY_RECEIVED if any_received else PurchaseStatus.ORDERED
    )
    db.add(purchase)
    await write_audit_log(
        db,
        actor_id=actor_id,
        action="RECEIVE",
        entity_name="Purchase",
        entity_id=purchase.id,
        metadata={"receipt_number": receipt.receipt_number},
    )
    await db.flush()
    return receipt

