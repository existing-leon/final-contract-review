from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core import response
from app.core.database import get_db
from app.core.exceptions import BizException
from app.models import ApprovalAttachment
from app.schemas.attachment import AttachmentOut, DownloadRequest
from app.services import attachment_service

router = APIRouter()


@router.get("/tasks/{task_id}/attachments")
def list_attachments(task_id: int, db: Session = Depends(get_db)):
    items = attachment_service.list_attachments(db, task_id)
    return response.success([AttachmentOut.model_validate(a).model_dump() for a in items])


@router.post("/tasks/{task_id}/attachments/{attachment_id}/download")
def download(
    task_id: int,
    attachment_id: str,
    body: DownloadRequest,
    db: Session = Depends(get_db),
):
    att = attachment_service.download_and_save(
        db, task_id, attachment_id, body.instance_id, body.file_name
    )
    return response.success(AttachmentOut.model_validate(att).model_dump())


@router.get("/attachments/{attachment_id}/file")
def get_file(attachment_id: int, db: Session = Depends(get_db)):
    att = db.get(ApprovalAttachment, attachment_id)
    if not att or not att.file_path:
        raise BizException(1002, "附件不存在")
    return FileResponse(att.file_path, filename=att.file_name or "attachment")
