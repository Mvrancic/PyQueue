from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pyqueue.api.schemas.job_requests import CreateJobRequest
from pyqueue.api.schemas.job_responses import JobResponse
from pyqueue.infra.db.session import get_db
from pyqueue.services.job_service import JobService

router = APIRouter()

def get_job_service(db: Session = Depends(get_db)) -> JobService:
    return JobService(db)

@router.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(
    request: CreateJobRequest,
    service: JobService = Depends(get_job_service)
):
    return service.create_job(request)

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: UUID,
    service: JobService = Depends(get_job_service)
):
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(
    status: Optional[str] = None,
    limit: int = 20,
    service: JobService = Depends(get_job_service)
):
    return service.list_jobs(limit=limit, status=status)

@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(
    job_id: UUID,
    service: JobService = Depends(get_job_service)
):
    job = service.cancel_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
def retry_job(
    job_id: UUID,
    service: JobService = Depends(get_job_service)
):
    job = service.retry_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
