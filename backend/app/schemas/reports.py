from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ReportSummaryResponse(BaseModel):
    start_date: date
    end_date: date
    purchase_total: Decimal
    waste_total: Decimal
    inventory_value: Decimal
    purchase_count: int
    receipt_count: int
    issue_count: int
    waste_count: int


class ReportExportRequest(BaseModel):
    start_date: date
    end_date: date
    format: str = Field(pattern="^(pdf|xlsx)$")

