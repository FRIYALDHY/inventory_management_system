import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import decode_token
from app.db.session import get_db
from app.domain.enums import UserRole
from app.domain.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise AppError(
            str(exc),
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token",
        ) from exc

    if payload.get("typ") != "access":
        raise AppError(
            "Token akses tidak valid",
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token_type",
        )

    try:
        user_id = uuid.UUID(str(payload.get("sub")))
    except (TypeError, ValueError) as exc:
        raise AppError(
            "Subjek token tidak valid",
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token_subject",
        ) from exc

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise AppError(
            "User tidak ditemukan atau nonaktif",
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="inactive_user",
        )

    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise AppError(
                "Anda tidak memiliki akses untuk aksi ini",
                status_code=status.HTTP_403_FORBIDDEN,
                code="forbidden",
            )
        return current_user

    return dependency


OwnerOnly = Depends(require_roles(UserRole.OWNER))
OwnerOrPurchase = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE))
OwnerOrGudang = Depends(require_roles(UserRole.OWNER, UserRole.GUDANG))
AllRoles = Depends(require_roles(UserRole.OWNER, UserRole.PURCHASE, UserRole.GUDANG))


async def touch_last_login(db: AsyncSession, user: User) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    await db.flush()
