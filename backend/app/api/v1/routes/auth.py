import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, touch_last_login
from app.core.exceptions import AppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    token_hash,
    verify_password,
)
from app.db.session import get_db
from app.domain.models import RefreshToken, User
from app.schemas.auth import CurrentUserResponse, LoginRequest, RefreshRequest, TokenResponse
from app.schemas.common import MessageResponse

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user dan terbitkan JWT",
    status_code=status.HTTP_200_OK,
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = (
        await db.execute(select(User).where(User.email == payload.email.lower()))
    ).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise AppError(
            "Email atau password salah",
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_credentials",
        )
    if not user.is_active:
        raise AppError(
            "User nonaktif",
            status_code=status.HTTP_403_FORBIDDEN,
            code="inactive_user",
        )

    access_token, access_expires_at, _ = create_access_token(str(user.id), user.role.value)
    refresh_token, refresh_expires_at, _ = create_refresh_token(str(user.id), user.role.value)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_hash(refresh_token),
            expires_at=refresh_expires_at,
        )
    )
    await touch_last_login(db, user)
    await db.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=access_expires_at,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Rotasi refresh token")
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise AppError(
            str(exc),
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_refresh_token",
        ) from exc

    if decoded.get("typ") != "refresh":
        raise AppError(
            "Token refresh tidak valid",
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token_type",
        )

    token_row = (
        await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash(payload.refresh_token))
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if not token_row or token_row.revoked_at or token_row.expires_at <= now:
        raise AppError(
            "Refresh token sudah tidak berlaku",
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="revoked_refresh_token",
        )

    user = await db.get(User, uuid.UUID(str(decoded["sub"])))
    if not user or not user.is_active:
        raise AppError(
            "User tidak ditemukan atau nonaktif",
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="inactive_user",
        )

    token_row.revoked_at = now
    access_token, access_expires_at, _ = create_access_token(str(user.id), user.role.value)
    new_refresh, refresh_expires_at, _ = create_refresh_token(str(user.id), user.role.value)
    db.add(token_row)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_hash(new_refresh),
            expires_at=refresh_expires_at,
        )
    )
    await db.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_at=access_expires_at,
    )


@router.post("/logout", response_model=MessageResponse, summary="Logout dan revoke refresh token")
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    token_row = (
        await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash(payload.refresh_token))
        )
    ).scalar_one_or_none()
    if token_row and not token_row.revoked_at:
        token_row.revoked_at = datetime.now(timezone.utc)
        db.add(token_row)
        await db.commit()
    return MessageResponse(message="Logout berhasil")


@router.get("/me", response_model=CurrentUserResponse, summary="Ambil profil user aktif")
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user

