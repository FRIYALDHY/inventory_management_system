from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import require_roles
from app.core.exceptions import AppError
from app.db.session import get_db
from app.domain.enums import UserRole
from app.domain.models import InventoryBalance, Item, ItemCategory, Supplier, Unit, User
from app.schemas.common import Page
from app.schemas.master import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
    UnitCreate,
    UnitResponse,
    UnitUpdate,
)
from app.services.audit import write_audit_log

router = APIRouter()


@router.get(
    "/suppliers",
    response_model=Page[SupplierResponse],
    summary="List supplier",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def list_suppliers(
    q: str | None = None,
    active_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[SupplierResponse]:
    filters = []
    if q:
        filters.append(Supplier.name.ilike(f"%{q}%"))
    if active_only:
        filters.append(Supplier.is_active.is_(True))
    statement = select(Supplier).where(*filters)
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    suppliers = (
        await db.execute(
            statement.order_by(Supplier.name.asc()).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return Page(items=suppliers, total=total or 0, page=page, page_size=page_size)


@router.post(
    "/suppliers",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat supplier",
)
async def create_supplier(
    payload: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE)),
) -> Supplier:
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    await db.flush()
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="CREATE",
        entity_name="Supplier",
        entity_id=supplier.id,
        metadata={"name": supplier.name},
    )
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.patch("/suppliers/{supplier_id}", response_model=SupplierResponse, summary="Update supplier")
async def update_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE)),
) -> Supplier:
    supplier = await db.get(Supplier, supplier_id)
    if not supplier:
        raise AppError("Supplier tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(supplier, field, value)
    db.add(supplier)
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="UPDATE",
        entity_name="Supplier",
        entity_id=supplier.id,
        metadata={"fields": list(data.keys())},
    )
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    summary="List kategori barang",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[ItemCategory]:
    return (await db.execute(select(ItemCategory).order_by(ItemCategory.name.asc()))).scalars().all()


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat kategori barang",
)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE)),
) -> ItemCategory:
    category = ItemCategory(**payload.model_dump())
    db.add(category)
    await db.flush()
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="CREATE",
        entity_name="ItemCategory",
        entity_id=category.id,
        metadata={"name": category.name},
    )
    await db.commit()
    await db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryResponse, summary="Update kategori")
async def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE)),
) -> ItemCategory:
    category = await db.get(ItemCategory, category_id)
    if not category:
        raise AppError("Kategori tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(category, field, value)
    db.add(category)
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="UPDATE",
        entity_name="ItemCategory",
        entity_id=category.id,
        metadata={"fields": list(data.keys())},
    )
    await db.commit()
    await db.refresh(category)
    return category


@router.get(
    "/units",
    response_model=list[UnitResponse],
    summary="List satuan barang",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def list_units(db: AsyncSession = Depends(get_db)) -> list[Unit]:
    return (await db.execute(select(Unit).order_by(Unit.name.asc()))).scalars().all()


@router.post(
    "/units",
    response_model=UnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat satuan barang",
)
async def create_unit(
    payload: UnitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE)),
) -> Unit:
    unit = Unit(**payload.model_dump())
    db.add(unit)
    await db.flush()
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="CREATE",
        entity_name="Unit",
        entity_id=unit.id,
        metadata={"symbol": unit.symbol},
    )
    await db.commit()
    await db.refresh(unit)
    return unit


@router.patch("/units/{unit_id}", response_model=UnitResponse, summary="Update satuan barang")
async def update_unit(
    unit_id: UUID,
    payload: UnitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE)),
) -> Unit:
    unit = await db.get(Unit, unit_id)
    if not unit:
        raise AppError("Satuan tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(unit, field, value)
    db.add(unit)
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="UPDATE",
        entity_name="Unit",
        entity_id=unit.id,
        metadata={"fields": list(data.keys())},
    )
    await db.commit()
    await db.refresh(unit)
    return unit


@router.get(
    "/items",
    response_model=Page[ItemResponse],
    summary="List master barang beserta stok",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def list_items(
    q: str | None = None,
    active_only: bool = False,
    low_stock: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[ItemResponse]:
    filters = []
    if q:
        filters.append(or_(Item.sku.ilike(f"%{q}%"), Item.name.ilike(f"%{q}%")))
    if active_only:
        filters.append(Item.is_active.is_(True))
    if low_stock:
        filters.append(InventoryBalance.current_quantity <= Item.minimum_stock)
    statement = (
        select(Item)
        .outerjoin(InventoryBalance, InventoryBalance.item_id == Item.id)
        .where(*filters)
        .options(selectinload(Item.category), selectinload(Item.unit), selectinload(Item.balance))
    )
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    items = (
        await db.execute(
            statement.order_by(Item.name.asc()).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().unique().all()
    return Page(items=items, total=total or 0, page=page, page_size=page_size)


@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Detail master barang",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))],
)
async def get_item(item_id: UUID, db: AsyncSession = Depends(get_db)) -> Item:
    item = (
        await db.execute(
            select(Item)
            .where(Item.id == item_id)
            .options(selectinload(Item.category), selectinload(Item.unit), selectinload(Item.balance))
        )
    ).scalar_one_or_none()
    if not item:
        raise AppError("Barang tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    return item


@router.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat master barang",
)
async def create_item(
    payload: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE)),
) -> Item:
    unit = await db.get(Unit, payload.unit_id)
    if not unit:
        raise AppError("Satuan tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    if payload.category_id and not await db.get(ItemCategory, payload.category_id):
        raise AppError("Kategori tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)

    item = Item(**payload.model_dump())
    db.add(item)
    await db.flush()
    db.add(InventoryBalance(item_id=item.id, current_quantity=0, average_cost=item.default_cost))
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="CREATE",
        entity_name="Item",
        entity_id=item.id,
        metadata={"sku": item.sku},
    )
    await db.commit()
    return await get_item(item.id, db)


@router.patch("/items/{item_id}", response_model=ItemResponse, summary="Update master barang")
async def update_item(
    item_id: UUID,
    payload: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE)),
) -> Item:
    item = await db.get(Item, item_id)
    if not item:
        raise AppError("Barang tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    data = payload.model_dump(exclude_unset=True)
    if data.get("unit_id") and not await db.get(Unit, data["unit_id"]):
        raise AppError("Satuan tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    if data.get("category_id") and not await db.get(ItemCategory, data["category_id"]):
        raise AppError("Kategori tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    for field, value in data.items():
        setattr(item, field, value)
    db.add(item)
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="UPDATE",
        entity_name="Item",
        entity_id=item.id,
        metadata={"fields": list(data.keys())},
    )
    await db.commit()
    return await get_item(item.id, db)
