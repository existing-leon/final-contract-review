from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AttachmentOut(BaseModel):
    id: int
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    download_status: str = "pending"
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DownloadRequest(BaseModel):
    instance_id: str
    file_name: Optional[str] = None


class DownloadResult(BaseModel):
    attachment_id: int
    file_path: str
    checksum: Optional[str] = None
    file_size: Optional[int] = None
