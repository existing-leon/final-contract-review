from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TaskLogOut(BaseModel):
    id: int
    task_id: int
    log_level: str
    log_type: str
    log_content: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
