from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import require_roles
from app.db.session import get_db
from app.domain.enums import UserRole
from app.domain.models import (
    InventoryBalance,
    InventoryIssue,
    InventoryReceipt,
    Item,
    StockAlert,
    StockMovement,
    Unit,
    User,
)
from app.schemas.common import Page
from app.schemas.inventory import (
    InventoryBalanceRow,
    InventoryIssueCreate,
    InventoryIssueResponse,
    InventoryReceiptCreate,
    InventoryReceiptResponse,
    StockAlertResponse,
    StockMovementResponse,
)
from app.services.inventory import create_issue, create_manual_receipt

router = APIRouter()


@router.get(
    "/balances",
    response_model=Page[InventoryBalanceRow],
    summary="List stok aktual inventory",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def list_balances(
    q: str | None = None,
    low_stock: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[InventoryBalanceRow]:
    filters = [Item.is_active.is_(True)]
    if q:
        filters.append(or_(Item.sku.ilike(f"%{q}%"), Item.name.ilike(f"%{q}%")))
    if low_stock:
        filters.append(InventoryBalance.current_quantity <= Item.minimum_stock)

    statement = (
        select(Item, Unit, InventoryBalance)
        .join(Unit, Unit.id == Item.unit_id)
        .outerjoin(InventoryBalance, InventoryBalance.item_id == Item.id)
        .where(*filters)
    )
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = (
        await db.execute(
            statement.order_by(Item.name.asc()).offset((page - 1) * page_size).limit(page_size)
        )
    ).all()
    items: list[InventoryBalanceRow] = []
    for item, unit, balance in rows:
        current_quantity = balance.current_quantity if balance else Decimal("0")
        average_cost = balance.average_cost if balance else item.default_cost
        inventory_value = current_quantity * average_cost
        items.append(
            InventoryBalanceRow(
                item_id=item.id,
                sku=item.sku,
                item_name=item.name,
                unit_symbol=unit.symbol,
                current_quantity=current_quantity,
                minimum_stock=item.minimum_stock,
                reorder_level=item.reorder_level,
                average_cost=average_cost,
                inventory_value=inventory_value,
                last_movement_at=balance.last_movement_at if balance else None,
                is_low_stock=current_quantity <= item.minimum_stock,
            )
        )
    return Page(items=items, total=total or 0, page=page, page_size=page_size)


@router.get(
    "/movements",
    response_model=Page[StockMovementResponse],
    summary="Ledger pergerakan stok",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def list_movements(
    item_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[StockMovementResponse]:
    filters = []
    if item_id:
        filters.append(StockMovement.item_id == item_id)
    statement = select(StockMovement).where(*filters)
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    movements = (
        await db.execute(
            statement.order_by(StockMovement.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return Page(items=movements, total=total or 0, page=page, page_size=page_size)


@router.post(
    "/receipts",
    response_model=InventoryReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Input barang masuk manual",
)
async def create_receipt_route(
    payload: InventoryReceiptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.GUDANG)),
) -> InventoryReceipt:
    receipt = await create_manual_receipt(db, payload, current_user.id)
    await db.commit()
    await db.refresh(receipt, attribute_names=["items"])
    return receipt


@router.get(
    "/receipts",
    response_model=Page[InventoryReceiptResponse],
    summary="List barang masuk",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def list_receipts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[InventoryReceiptResponse]:
    statement = select(InventoryReceipt).options(selectinload(InventoryReceipt.items))
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    receipts = (
        await db.execute(
            statement.order_by(InventoryReceipt.receipt_date.desc(), InventoryReceipt.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().unique().all()
    return Page(items=receipts, total=total or 0, page=page, page_size=page_size)


@router.post(
    "/issues",
    response_model=InventoryIssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Input barang keluar",
)
async def create_issue_route(
    payload: InventoryIssueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.GUDANG)),
) -> InventoryIssue:
    issue = await create_issue(db, payload, current_user.id)
    await db.commit()
    await db.refresh(issue, attribute_names=["items"])
    return issue


@router.get(
    "/issues",
    response_model=Page[InventoryIssueResponse],
    summary="List barang keluar",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def list_issues(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[InventoryIssueResponse]:
    statement = select(InventoryIssue).options(selectinload(InventoryIssue.items))
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    issues = (
        await db.execute(
            statement.order_by(InventoryIssue.issue_date.desc(), InventoryIssue.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().unique().all()
    return Page(items=issues, total=total or 0, page=page, page_size=page_size)


@router.get(
    "/alerts",
    response_model=Page[StockAlertResponse],
    summary="List stock alert",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def list_alerts(
    active_only: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[StockAlertResponse]:
    filters = []
    if active_only:
        filters.append(StockAlert.is_active.is_(True))
    statement = select(StockAlert).where(*filters)
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    alerts = (
        await db.execute(
            statement.order_by(StockAlert.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return Page(items=alerts, total=total or 0, page=page, page_size=page_size)
