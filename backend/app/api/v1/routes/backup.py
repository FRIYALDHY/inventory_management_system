from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_roles
from app.core.exceptions import AppError
from app.db.session import get_db
from app.domain.enums import UserRole
from app.domain.models import BackupJob, User
from app.schemas.common import Page
from app.schemas.jobs import BackupJobResponse
from app.services.backup import create_database_backup

router = APIRouter()


@router.post(
    "",
    response_model=BackupJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat backup database PostgreSQL",
)
async def create_backup_route(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER)),
) -> BackupJob:
    job = await create_database_backup(db, current_user.id)
    await db.commit()
    return job


@router.get(
    "",
    response_model=Page[BackupJobResponse],
    summary="Histori backup database",
    dependencies=[Depends(require_roles(UserRole.OWNER))],
)
async def list_backups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[BackupJobResponse]:
    statement = select(BackupJob)
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = (
        await db.execute(
            statement.order_by(BackupJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return Page(items=rows, total=total or 0, page=page, page_size=page_size)


@router.get(
    "/{backup_id}/download",
    summary="Download file backup database",
    dependencies=[Depends(require_roles(UserRole.OWNER))],
)
async def download_backup(backup_id: UUID, db: AsyncSession = Depends(get_db)) -> FileResponse:
    job = await db.get(BackupJob, backup_id)
    if not job or not job.file_path:
        raise AppError("Backup tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    path = Path(job.file_path)
    if not path.exists():
        raise AppError("File backup tidak tersedia di server", status_code=status.HTTP_404_NOT_FOUND)
    return FileResponse(path, filename=path.name)
