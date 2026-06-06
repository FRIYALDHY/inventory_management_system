from uuid import UUID

from app.domain.enums import JobStatus
from app.schemas.common import Timestamped


class ExportJobResponse(Timestamped):
    id: UUID
    report_type: str
    file_format: str
    status: JobStatus
    file_path: str | None
    error_message: str | None


class BackupJobResponse(Timestamped):
    id: UUID
    status: JobStatus
    file_path: str | None
    file_size_bytes: int | None
    error_message: str | None

