from uuid import UUID

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.domain.enums import MovementType
from app.domain.models import (
    InventoryIssue,
    InventoryIssueItem,
    InventoryReceipt,
    InventoryReceiptItem,
    Item,
)
from app.schemas.inventory import InventoryIssueCreate, InventoryReceiptCreate
from app.services.audit import write_audit_log
from app.services.stock import create_stock_movement, get_or_create_balance


async def create_manual_receipt(
    db: AsyncSession,
    payload: InventoryReceiptCreate,
    actor_id: UUID,
) -> InventoryReceipt:
    item_ids = [item.item_id for item in payload.items]
    if len(item_ids) != len(set(item_ids)):
        raise AppError("Item barang masuk tidak boleh duplikat")

    active_count = len(
        (await db.execute(select(Item.id).where(Item.id.in_(item_ids), Item.is_active.is_(True)))).all()
    )
    if active_count != len(item_ids):
        raise AppError("Satu atau lebih barang tidak ditemukan/nonaktif", status_code=status.HTTP_404_NOT_FOUND)

    receipt = InventoryReceipt(
        receipt_number=payload.receipt_number,
        receipt_date=payload.receipt_date,
        notes=payload.notes,
        created_by_id=actor_id,
    )
    db.add(receipt)
    await db.flush()

    for item in payload.items:
        receipt_item = InventoryReceiptItem(
            receipt_id=receipt.id,
            item_id=item.item_id,
            quantity=item.quantity,
            unit_cost=item.unit_cost,
        )
        db.add(receipt_item)
        await create_stock_movement(
            db,
            item_id=item.item_id,
            movement_type=MovementType.MANUAL_IN,
            quantity_change=item.quantity,
            unit_cost=item.unit_cost,
            reference_type="InventoryReceipt",
            reference_id=receipt.id,
            note=f"Manual receipt {receipt.receipt_number}",
            performed_by_id=actor_id,
        )

    await write_audit_log(
        db,
        actor_id=actor_id,
        action="CREATE",
        entity_name="InventoryReceipt",
        entity_id=receipt.id,
        metadata={"receipt_number": receipt.receipt_number},
    )
    return receipt


async def create_issue(db: AsyncSession, payload: InventoryIssueCreate, actor_id: UUID) -> InventoryIssue:
    item_ids = [item.item_id for item in payload.items]
    if len(item_ids) != len(set(item_ids)):
        raise AppError("Item barang keluar tidak boleh duplikat")

    issue = InventoryIssue(
        issue_number=payload.issue_number,
        issue_date=payload.issue_date,
        destination=payload.destination,
        notes=payload.notes,
        created_by_id=actor_id,
    )
    db.add(issue)
    await db.flush()

    for item in payload.items:
        balance = await get_or_create_balance(db, item.item_id)
        issue_item = InventoryIssueItem(
            issue_id=issue.id,
            item_id=item.item_id,
            quantity=item.quantity,
            unit_cost=balance.average_cost,
        )
        db.add(issue_item)
        await create_stock_movement(
            db,
            item_id=item.item_id,
            movement_type=MovementType.OUT,
            quantity_change=-item.quantity,
            unit_cost=balance.average_cost,
            reference_type="InventoryIssue",
            reference_id=issue.id,
            note=f"Inventory issue {issue.issue_number}",
            performed_by_id=actor_id,
        )

    await write_audit_log(
        db,
        actor_id=actor_id,
        action="CREATE",
        entity_name="InventoryIssue",
        entity_id=issue.id,
        metadata={"issue_number": issue.issue_number},
    )
    return issue

