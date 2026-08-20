from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from pyqueue.domain.models import JobStatus
from pyqueue.infra.db.models import Job
from pyqueue.api.schemas.job_requests import CreateJobRequest
from pyqueue.infra.queue.redis_queue import queue_client

class JobService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, request: CreateJobRequest) -> Job:
        job = Job(
            type=request.type.value,
            payload=request.payload,
            max_retries=request.max_retries,
            client_request_id=request.client_request_id,
            status=JobStatus.QUEUED.value
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # Enqueue to Redis
        queue_client.enqueue(str(job.id))
        
        return job

    def get_job(self, job_id: UUID) -> Optional[Job]:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def list_jobs(self, limit: int = 20, status: Optional[str] = None) -> List[Job]:
        query = self.db.query(Job)
        if status:
            query = query.filter(Job.status == status)
        return query.limit(limit).all()

    def cancel_job(self, job_id: UUID) -> Optional[Job]:
        job = self.get_job(job_id)
        if not job:
            return None
        
        # Only cancel if queued or running
        if job.status in [JobStatus.QUEUED.value, JobStatus.RUNNING.value]:
            job.status = JobStatus.CANCELED.value
            job.canceled_at = datetime.now(timezone.utc)
            job.finished_at = datetime.now(timezone.utc) # Technically finished if canceled (simple model)
            self.db.commit()
            self.db.refresh(job)
        return job

    def retry_job(self, job_id: UUID) -> Optional[Job]:
        job = self.get_job(job_id)
        if not job:
            return None
        
        # Only retry if failed or canceled
        if job.status not in [JobStatus.FAILED.value, JobStatus.CANCELED.value]:
            return job # Or raise error? For now, idempotent return

        # Reset state to queued. retry_count is bumped by process_job() when
        # the retried execution actually fails, not here, to avoid double
        # counting the same retry.
        job.status = JobStatus.QUEUED.value
        job.result = None
        job.error = None
        job.started_at = None
        job.finished_at = None

        self.db.commit()
        self.db.refresh(job)
        
        # Re-enqueue
        queue_client.enqueue(str(job.id))
        
        return job
