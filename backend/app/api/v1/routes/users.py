from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_roles
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.db.session import get_db
from app.domain.enums import UserRole
from app.domain.models import User
from app.schemas.common import Page
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.services.audit import write_audit_log

router = APIRouter()


@router.get(
    "",
    response_model=Page[UserResponse],
    summary="List user",
    dependencies=[Depends(require_roles(UserRole.OWNER))],
)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[UserResponse]:
    offset = (page - 1) * page_size
    total = await db.scalar(select(func.count(User.id)))
    users = (
        await db.execute(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
        )
    ).scalars().all()
    return Page(items=users, total=total or 0, page=page, page_size=page_size)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat user baru",
)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER)),
) -> User:
    existing = await db.scalar(select(User.id).where(User.email == payload.email.lower()))
    if existing:
        raise AppError("Email sudah digunakan", status_code=status.HTTP_409_CONFLICT)
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    await db.flush()
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="CREATE",
        entity_name="User",
        entity_id=user.id,
        metadata={"email": user.email, "role": user.role.value},
    )
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user")
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER)),
) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise AppError("User tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)

    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.hashed_password = hash_password(data.pop("password"))
    for field, value in data.items():
        setattr(user, field, value)
    db.add(user)
    await write_audit_log(
        db,
        actor_id=current_user.id,
        action="UPDATE",
        entity_name="User",
        entity_id=user.id,
        metadata={"fields": list(data.keys())},
    )
    await db.commit()
    await db.refresh(user)
    return user
