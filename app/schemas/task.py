from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TaskOut(BaseModel):
    id: int
    approval_code: str
    approval_title: Optional[str] = None
    applicant_name: Optional[str] = None
    task_status: str
    write_status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RetryRequest(BaseModel):
    resume_from: Optional[str] = None  # parsing / reviewing
