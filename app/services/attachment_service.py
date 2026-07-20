"""附件模块：附件下载、存储、元数据保存。"""
import os

from sqlalchemy.orm import Session

from app.core.constants import DownloadStatus, LogLevel, LogType
from app.models import ApprovalAttachment
from app.services import log_service
from app.tools import download_contract_attachment


def list_attachments(db: Session, task_id: int) -> list[ApprovalAttachment]:
    return (
        db.query(ApprovalAttachment)
        .filter(ApprovalAttachment.task_id == task_id)
        .order_by(ApprovalAttachment.id.asc())
        .all()
    )


def _infer_file_type(file_name: str | None) -> str:
    if not file_name:
        return ""
    return os.path.splitext(file_name)[1].lstrip(".").lower()


def download_and_save(
    db: Session,
    task_id: int,
    attachment_id: str,
    instance_id: str,
    file_name: str | None = None,
) -> ApprovalAttachment:
    result = download_contract_attachment(instance_id, attachment_id, file_name)
    name = result.get("file_name", file_name or "")
    attachment = ApprovalAttachment(
        task_id=task_id,
        file_name=name,
        file_type=_infer_file_type(name),
        file_path=result["file_path"],
        file_size=result.get("file_size"),
        checksum=result.get("checksum"),
        download_status=DownloadStatus.SUCCESS,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    log_service.log(
        db, task_id, LogLevel.INFO, LogType.DOWNLOAD,
        f"附件下载成功: {name} ({result.get('file_size')} bytes)",
    )
    return attachment
