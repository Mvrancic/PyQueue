from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from pyqueue.domain.models import JobType

class CreateJobRequest(BaseModel):
    type: JobType
    payload: Dict[str, Any]
    max_retries: int = Field(default=0, ge=0)
    client_request_id: Optional[str] = None
