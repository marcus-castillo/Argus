"""Background job repository with atomic claim semantics."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update

from app.models.enums import JobStatus
from app.models.job import ProcessingJob
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[ProcessingJob]):
    model = ProcessingJob

    async def claim_next(self) -> ProcessingJob | None:
        """Atomically claim one pending job using ``FOR UPDATE SKIP LOCKED``.

        This makes the queue safe to run with multiple worker processes.
        """
        stmt = (
            select(ProcessingJob)
            .where(ProcessingJob.status == JobStatus.PENDING)
            .order_by(ProcessingJob.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job = await self.session.scalar(stmt)
        if job is None:
            return None
        job.status = JobStatus.RUNNING
        job.attempts += 1
        job.locked_at = datetime.now(timezone.utc)
        await self.session.flush()
        return job

    async def mark_succeeded(self, job: ProcessingJob) -> None:
        job.status = JobStatus.SUCCEEDED
        job.last_error = None

    async def mark_failed(self, job: ProcessingJob, error: str) -> None:
        job.last_error = error[:4000]
        if job.attempts >= job.max_attempts:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.PENDING  # retry on next poll
            job.locked_at = None

    async def reset_stale_running(self, older_than_seconds: int = 600) -> int:
        """Requeue jobs stuck in RUNNING (e.g. after a worker crash)."""
        cutoff = datetime.now(timezone.utc).timestamp() - older_than_seconds
        stmt = (
            update(ProcessingJob)
            .where(
                ProcessingJob.status == JobStatus.RUNNING,
                ProcessingJob.locked_at.is_not(None),
                func_epoch(ProcessingJob.locked_at) < cutoff,
            )
            .values(status=JobStatus.PENDING, locked_at=None)
        )
        result = await self.session.execute(stmt)
        return result.rowcount or 0


def func_epoch(col):  # pragma: no cover - tiny SQL helper
    from sqlalchemy import func

    return func.extract("epoch", col)
