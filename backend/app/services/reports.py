from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.enums import JobStatus
from app.domain.models import (
    ExportJob,
    InventoryBalance,
    InventoryIssue,
    InventoryReceipt,
    Purchase,
    WasteItem,
    WasteRecord,
)
from app.schemas.reports import ReportSummaryResponse


async def build_report_summary(
    db: AsyncSession,
    *,
    start_date: date,
    end_date: date,
) -> ReportSummaryResponse:
    purchase_total = await db.scalar(
        select(func.coalesce(func.sum(Purchase.total_amount), 0)).where(
            Purchase.purchase_date >= start_date,
            Purchase.purchase_date <= end_date,
        )
    )
    waste_total = await db.scalar(
        select(func.coalesce(func.sum(WasteItem.estimated_cost), 0))
        .join(WasteRecord, WasteRecord.id == WasteItem.waste_id)
        .where(WasteRecord.waste_date >= start_date, WasteRecord.waste_date <= end_date)
    )
    inventory_value = await db.scalar(
        select(
            func.coalesce(
                func.sum(InventoryBalance.current_quantity * InventoryBalance.average_cost), 0
            )
        )
    )
    purchase_count = await db.scalar(
        select(func.count(Purchase.id)).where(
            Purchase.purchase_date >= start_date,
            Purchase.purchase_date <= end_date,
        )
    )
    receipt_count = await db.scalar(
        select(func.count(InventoryReceipt.id)).where(
            InventoryReceipt.receipt_date >= start_date,
            InventoryReceipt.receipt_date <= end_date,
        )
    )
    issue_count = await db.scalar(
        select(func.count(InventoryIssue.id)).where(
            InventoryIssue.issue_date >= start_date,
            InventoryIssue.issue_date <= end_date,
        )
    )
    waste_count = await db.scalar(
        select(func.count(WasteRecord.id)).where(
            WasteRecord.waste_date >= start_date,
            WasteRecord.waste_date <= end_date,
        )
    )

    return ReportSummaryResponse(
        start_date=start_date,
        end_date=end_date,
        purchase_total=purchase_total or Decimal("0"),
        waste_total=waste_total or Decimal("0"),
        inventory_value=inventory_value or Decimal("0"),
        purchase_count=purchase_count or 0,
        receipt_count=receipt_count or 0,
        issue_count=issue_count or 0,
        waste_count=waste_count or 0,
    )


def _export_filename(start_date: date, end_date: date, file_format: str) -> Path:
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return settings.export_dir / f"inventory-report-{start_date}-{end_date}-{stamp}.{file_format}"


async def export_report(
    db: AsyncSession,
    *,
    start_date: date,
    end_date: date,
    file_format: str,
    actor_id: UUID,
) -> ExportJob:
    job = ExportJob(
        report_type="inventory_summary",
        file_format=file_format,
        status=JobStatus.PROCESSING,
        requested_by_id=actor_id,
    )
    db.add(job)
    await db.flush()
    try:
        summary = await build_report_summary(db, start_date=start_date, end_date=end_date)
        file_path = _export_filename(start_date, end_date, file_format)
        if file_format == "xlsx":
            _write_xlsx(file_path, summary)
        else:
            _write_pdf(file_path, summary)
        job.status = JobStatus.SUCCESS
        job.file_path = str(file_path)
    except Exception as exc:  # pragma: no cover - persisted for operator diagnostics
        job.status = JobStatus.FAILED
        job.error_message = str(exc)
    finally:
        db.add(job)
        await db.flush()
    return job


def _write_xlsx(path: Path, summary: ReportSummaryResponse) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Inventory Report"
    sheet.append(["ATA Cafe & Billiard PIMS Report"])
    sheet.append(["Start Date", str(summary.start_date)])
    sheet.append(["End Date", str(summary.end_date)])
    sheet.append([])
    sheet.append(["Metric", "Value"])
    sheet.append(["Purchase Total", float(summary.purchase_total)])
    sheet.append(["Waste Total", float(summary.waste_total)])
    sheet.append(["Inventory Value", float(summary.inventory_value)])
    sheet.append(["Purchase Count", summary.purchase_count])
    sheet.append(["Receipt Count", summary.receipt_count])
    sheet.append(["Issue Count", summary.issue_count])
    sheet.append(["Waste Count", summary.waste_count])
    workbook.save(path)


def _write_pdf(path: Path, summary: ReportSummaryResponse) -> None:
    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 72
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(72, y, "ATA Cafe & Billiard PIMS Report")
    y -= 28
    pdf.setFont("Helvetica", 10)
    rows = [
        ("Start Date", str(summary.start_date)),
        ("End Date", str(summary.end_date)),
        ("Purchase Total", f"{summary.purchase_total:,.2f}"),
        ("Waste Total", f"{summary.waste_total:,.2f}"),
        ("Inventory Value", f"{summary.inventory_value:,.2f}"),
        ("Purchase Count", str(summary.purchase_count)),
        ("Receipt Count", str(summary.receipt_count)),
        ("Issue Count", str(summary.issue_count)),
        ("Waste Count", str(summary.waste_count)),
    ]
    for label, value in rows:
        pdf.drawString(72, y, label)
        pdf.drawRightString(width - 72, y, value)
        y -= 18
    pdf.save()
