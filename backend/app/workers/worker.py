"""Background worker: polls the ``processing_jobs`` queue and runs jobs.

Run as its own process/container:

    python -m app.workers.worker

Safe to run with N replicas — jobs are claimed with ``FOR UPDATE SKIP LOCKED``.
Each job runs in its own transaction; a crash mid-job leaves the row claimable
again via :meth:`JobRepository.reset_stale_running`.
"""
from __future__ import annotations

import asyncio
import signal

from app.core.config import settings
from app.core.db import SessionFactory
from app.core.logging import get_logger
from app.models.enums import DocumentStatus
from app.models.job import ProcessingJob
from app.repositories.document import DocumentRepository
from app.repositories.job import JobRepository
from app.services.processing_service import ProcessingService

logger = get_logger("worker")

_shutdown = asyncio.Event()


def _install_signal_handlers() -> None:
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown.set)
        except NotImplementedError:  # pragma: no cover - Windows
            signal.signal(sig, lambda *_: _shutdown.set())


async def _run_job(job: ProcessingJob) -> None:
    """Execute a single job in its own transaction."""
    async with SessionFactory() as session:
        jobs = JobRepository(session)
        # Re-attach the job to this session.
        job = await session.get(ProcessingJob, job.id)
        if job is None:
            return
        try:
            if job.job_type == "process_document" and job.document_id:
                processing = ProcessingService(session)
                count = await processing.process_document(job.document_id)
                logger.info("Job %s processed %d citations", job.id, count)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
            await jobs.mark_succeeded(job)
            await session.commit()
        except Exception as exc:  # noqa: BLE001 - we record the error
            await session.rollback()
            async with SessionFactory() as err_session:
                ejobs = JobRepository(err_session)
                ejob = await err_session.get(ProcessingJob, job.id)
                if ejob is not None:
                    await ejobs.mark_failed(ejob, repr(exc))
                    if ejob.status.value == "failed" and ejob.document_id:
                        await DocumentRepository(err_session).set_status(
                            ejob.document_id,
                            DocumentStatus.FAILED,
                            error_message=str(exc),
                        )
                    await err_session.commit()
            logger.exception("Job %s failed: %s", job.id, exc)


async def _claim_batch() -> list[ProcessingJob]:
    claimed: list[ProcessingJob] = []
    async with SessionFactory() as session:
        jobs = JobRepository(session)
        for _ in range(settings.worker_batch_size):
            job = await jobs.claim_next()
            if job is None:
                break
            claimed.append(job)
        await session.commit()
    return claimed


async def run() -> None:
    _install_signal_handlers()
    logger.info("Worker started (poll=%ss)", settings.worker_poll_interval_seconds)

    # On boot, requeue any jobs left RUNNING by a previous crashed worker.
    async with SessionFactory() as session:
        n = await JobRepository(session).reset_stale_running(older_than_seconds=0)
        await session.commit()
        if n:
            logger.info("Requeued %d stale running job(s)", n)

    while not _shutdown.is_set():
        batch = await _claim_batch()
        if not batch:
            try:
                await asyncio.wait_for(
                    _shutdown.wait(), timeout=settings.worker_poll_interval_seconds
                )
            except asyncio.TimeoutError:
                pass
            continue
        await asyncio.gather(*(_run_job(job) for job in batch))

    logger.info("Worker shutting down cleanly")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
