from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class PendingApprovalItem(BaseModel):
    approval_code: str
    approval_title: str = ""
    applicant_name: str = ""
    apply_time: Optional[str] = None
    attachment_count: int = 0


class PullRequest(BaseModel):
    limit: int = 20


class PullResult(BaseModel):
    pulled: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0


class ApprovalDetail(BaseModel):
    approval_code: str
    approval_title: str = ""
    applicant_name: str = ""
    apply_time: Optional[str] = None
    form_data: dict[str, Any] = {}
    current_status: str = ""
    attachments: list[dict[str, Any]] = []
