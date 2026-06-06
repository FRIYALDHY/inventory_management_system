from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import MovementType
from app.domain.models import WasteItem, WasteRecord
from app.schemas.waste import WasteCreate
from app.services.audit import write_audit_log
from app.services.stock import create_stock_movement, get_or_create_balance


async def create_waste(db: AsyncSession, payload: WasteCreate, actor_id: UUID) -> WasteRecord:
    item_ids = [item.item_id for item in payload.items]
    if len(item_ids) != len(set(item_ids)):
        raise AppError("Item waste tidak boleh duplikat")

    waste = WasteRecord(
        waste_number=payload.waste_number,
        waste_date=payload.waste_date,
        notes=payload.notes,
        created_by_id=actor_id,
    )
    db.add(waste)
    await db.flush()

    for item in payload.items:
        balance = await get_or_create_balance(db, item.item_id)
        estimated_cost = item.quantity * balance.average_cost
        waste_item = WasteItem(
            waste_id=waste.id,
            item_id=item.item_id,
            quantity=item.quantity,
            reason=item.reason,
            unit_cost=balance.average_cost,
            estimated_cost=estimated_cost,
        )
        db.add(waste_item)
        await create_stock_movement(
            db,
            item_id=item.item_id,
            movement_type=MovementType.WASTE,
            quantity_change=-item.quantity,
            unit_cost=balance.average_cost,
            reference_type="WasteRecord",
            reference_id=waste.id,
            note=f"Waste {waste.waste_number}: {item.reason}",
            performed_by_id=actor_id,
        )

    await write_audit_log(
        db,
        actor_id=actor_id,
        action="CREATE",
        entity_name="WasteRecord",
        entity_id=waste.id,
        metadata={"waste_number": waste.waste_number},
    )
    return waste
