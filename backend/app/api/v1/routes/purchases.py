from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import require_roles
from app.core.exceptions import AppError
from app.db.session import get_db
from app.domain.enums import PurchaseStatus, UserRole
from app.domain.models import Purchase, User
from app.schemas.common import Page
from app.schemas.inventory import InventoryReceiptResponse
from app.schemas.purchase import PurchaseCreate, PurchaseReceiveRequest, PurchaseResponse, PurchaseUpdate
from app.services.purchase import create_purchase, receive_purchase

router = APIRouter()


def _purchase_options():
    return (
        selectinload(Purchase.supplier),
        selectinload(Purchase.created_by),
        selectinload(Purchase.items),
    )


@router.get(
    "",
    response_model=Page[PurchaseResponse],
    summary="List purchase",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def list_purchases(
    status_filter: PurchaseStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[PurchaseResponse]:
    filters = []
    if status_filter:
        filters.append(Purchase.status == status_filter)
    statement = select(Purchase).where(*filters).options(*_purchase_options())
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    purchases = (
        await db.execute(
            statement.order_by(Purchase.purchase_date.desc(), Purchase.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().unique().all()
    return Page(items=purchases, total=total or 0, page=page, page_size=page_size)


@router.get(
    "/{purchase_id}",
    response_model=PurchaseResponse,
    summary="Detail purchase",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def get_purchase(purchase_id: UUID, db: AsyncSession = Depends(get_db)) -> Purchase:
    purchase = (
        await db.execute(
            select(Purchase).where(Purchase.id == purchase_id).options(*_purchase_options())
        )
    ).scalar_one_or_none()
    if not purchase:
        raise AppError("Purchase tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    return purchase


@router.post(
    "",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat purchase baru",
)
async def create_purchase_route(
    payload: PurchaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE)),
) -> Purchase:
    purchase = await create_purchase(db, payload, current_user.id)
    await db.commit()
    return await get_purchase(purchase.id, db)


@router.patch("/{purchase_id}", response_model=PurchaseResponse, summary="Update header purchase")
async def update_purchase(
    purchase_id: UUID,
    payload: PurchaseUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE)),
) -> Purchase:
    purchase = (
        await db.execute(
            select(Purchase).where(Purchase.id == purchase_id).options(selectinload(Purchase.items))
        )
    ).scalar_one_or_none()
    if not purchase:
        raise AppError("Purchase tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)

    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == PurchaseStatus.CANCELLED:
        if any(item.received_quantity > 0 for item in purchase.items):
            raise AppError("Purchase yang sudah diterima tidak bisa dibatalkan")
    for field, value in data.items():
        setattr(purchase, field, value)
    db.add(purchase)
    await db.commit()
    return await get_purchase(purchase.id, db)


@router.post(
    "/{purchase_id}/receive",
    response_model=InventoryReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Terima barang dari purchase dan update stok",
)
async def receive_purchase_route(
    purchase_id: UUID,
    payload: PurchaseReceiveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG)),
):
    receipt = await receive_purchase(db, purchase_id, payload, current_user.id)
    await db.commit()
    await db.refresh(receipt, attribute_names=["items"])
    return receipt
