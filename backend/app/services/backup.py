import subprocess
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.enums import JobStatus
from app.domain.models import BackupJob


async def create_database_backup(db: AsyncSession, actor_id: UUID) -> BackupJob:
    settings.backup_dir.mkdir(parents=True, exist_ok=True)
    file_path = settings.backup_dir / f"ata-pims-backup-{datetime.now():%Y%m%d%H%M%S}.dump"
    job = BackupJob(status=JobStatus.PROCESSING, requested_by_id=actor_id)
    db.add(job)
    await db.flush()

    try:
        subprocess.run(
            [
                "pg_dump",
                "--format=custom",
                f"--file={file_path}",
                settings.pg_dump_database_url,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        job.status = JobStatus.SUCCESS
        job.file_path = str(file_path)
        job.file_size_bytes = file_path.stat().st_size
    except Exception as exc:  # pragma: no cover - depends on installed pg_dump
        job.status = JobStatus.FAILED
        job.error_message = str(exc)
    finally:
        db.add(job)
        await db.flush()
    return job
