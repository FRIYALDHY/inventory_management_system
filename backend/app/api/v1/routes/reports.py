from datetime import date
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
from app.domain.models import ExportJob, User
from app.schemas.common import Page
from app.schemas.jobs import ExportJobResponse
from app.schemas.reports import ReportExportRequest, ReportSummaryResponse
from app.services.reports import build_report_summary, export_report

router = APIRouter()


@router.get(
    "/summary",
    response_model=ReportSummaryResponse,
    summary="Laporan ringkas harian/bulanan/tahunan berdasarkan range tanggal",
    dependencies=[Depends(require_roles(UserRole.OWNER))],
)
async def report_summary(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
) -> ReportSummaryResponse:
    if end_date < start_date:
        raise AppError("end_date harus sama atau setelah start_date")
    return await build_report_summary(db, start_date=start_date, end_date=end_date)


@router.post(
    "/export",
    response_model=ExportJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Export laporan inventory ke PDF atau Excel",
)
async def export_summary(
    payload: ReportExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OWNER)),
) -> ExportJob:
    if payload.end_date < payload.start_date:
        raise AppError("end_date harus sama atau setelah start_date")
    job = await export_report(
        db,
        start_date=payload.start_date,
        end_date=payload.end_date,
        file_format=payload.format,
        actor_id=current_user.id,
    )
    await db.commit()
    return job


@router.get(
    "/exports",
    response_model=Page[ExportJobResponse],
    summary="Histori export laporan",
    dependencies=[Depends(require_roles(UserRole.OWNER))],
)
async def list_exports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[ExportJobResponse]:
    statement = select(ExportJob)
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = (
        await db.execute(
            statement.order_by(ExportJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return Page(items=rows, total=total or 0, page=page, page_size=page_size)


@router.get(
    "/exports/{export_id}/download",
    summary="Download file export laporan",
    dependencies=[Depends(require_roles(UserRole.OWNER))],
)
async def download_export(export_id: UUID, db: AsyncSession = Depends(get_db)) -> FileResponse:
    job = await db.get(ExportJob, export_id)
    if not job or not job.file_path:
        raise AppError("File export tidak ditemukan", status_code=status.HTTP_404_NOT_FOUND)
    path = Path(job.file_path)
    if not path.exists():
        raise AppError("File export tidak tersedia di server", status_code=status.HTTP_404_NOT_FOUND)
    return FileResponse(path, filename=path.name)
