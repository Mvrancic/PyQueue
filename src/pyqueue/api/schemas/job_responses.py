from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel
from pyqueue.domain.models import JobStatus, JobType

class JobResponse(BaseModel):
    id: UUID
    type: JobType
    status: JobStatus
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    retry_count: int
    max_retries: int

    class Config:
        from_attributes = True
