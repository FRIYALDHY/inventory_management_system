from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import require_roles
from app.core.exceptions import AppError
from app.db.session import get_db
from app.domain.enums import UserRole
from app.domain.models import User, WasteRecord
from app.schemas.common import Page
from app.schemas.waste import WasteCreate, WasteResponse
from app.services.waste import create_waste

router = APIRouter()


@router.post(
    "",
    response_model=WasteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Input waste dan kurangi stok",
)
async def create_waste_route(
    payload: WasteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.GUDANG)),
) -> WasteRecord:
    waste = await create_waste(db, payload, current_user.id)
    await db.commit()
    await db.refresh(waste, attribute_names=["items"])
    return waste


@router.get(
    "",
    response_model=Page[WasteResponse],
    summary="List waste",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.GUDANG))],
)
async def list_waste(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[WasteResponse]:
    statement = select(WasteRecord).options(selectinload(WasteRecord.items))
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = (
        await db.execute(
            statement.order_by(WasteRecord.waste_date.desc(), WasteRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().unique().all()
    return Page(items=rows, total=total or 0, page=page, page_size=page_size)


@router.get(
    "/{waste_id}",
    response_model=WasteResponse,
    summary="Detail waste",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.GUDANG))],
)
async def get_waste(waste_id: UUID, db: AsyncSession = Depends(get_db)) -> WasteRecord:
    waste = (
        await db.execute(
            select(WasteRecord)
            .where(WasteRecord.id == waste_id)
            .options(selectinload(WasteRecord.items))
        )
    ).scalar_one_or_none()
    if not waste:
        raise AppError("Waste tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    return waste
