import time
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from pyqueue.infra.db.session import SessionLocal
from pyqueue.infra.queue.redis_queue import queue_client
from pyqueue.domain.models import JobStatus
from pyqueue.infra.db.models import Job
from pyqueue.services.task_registry import get_handler

logger = logging.getLogger("worker")
logging.basicConfig(level=logging.INFO)

def process_job(db: Session, job_id: str):
    logger.info(f"Processing job {job_id}")
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        logger.error(f"Job {job_id} not found in DB")
        return

    if job.status in [JobStatus.CANCELED.value, JobStatus.SUCCEEDED.value]:
        logger.info(f"Job {job_id} is already {job.status}, skipping")
        return

    # Update state to RUNNING
    job.status = JobStatus.RUNNING.value
    job.started_at = datetime.utcnow()
    db.commit()

    handler = get_handler(job.type)
    if not handler:
        logger.error(f"No handler for job type {job.type}")
        job.status = JobStatus.FAILED.value
        job.error = f"No handler for type {job.type}"
        job.finished_at = datetime.utcnow()
        db.commit()
        return

    try:
        result = handler(job.payload)
        job.result = result
        job.status = JobStatus.SUCCEEDED.value
    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        job.error = str(e)
        job.retry_count += 1
        
        if job.retry_count <= job.max_retries:
            logger.info(f"Retrying job {job_id} ({job.retry_count}/{job.max_retries})")
            job.status = JobStatus.QUEUED.value
            job.finished_at = None
            db.commit()
            queue_client.enqueue(str(job.id))
            return # Exit process_job, it will be picked up again
            
        job.status = JobStatus.FAILED.value
    finally:
        job.finished_at = datetime.utcnow()
        db.commit()
        logger.info(f"Job {job_id} finished with status {job.status}")

def run_worker():
    logger.info("Worker started, waiting for jobs...")
    while True:
        try:
            # Blocking pop with 2 second timeout to allow checking for signals/shutdown
            data = queue_client.dequeue(timeout=2)
            if data:
                job_id = data.get("job_id")
                if job_id:
                    with SessionLocal() as db:
                        process_job(db, job_id)
        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    run_worker()
