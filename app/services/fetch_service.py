"""拉取模块：拉取待处理审批单并按 approval_code 去重保存。"""
from sqlalchemy.orm import Session

from app.core.constants import LogLevel, LogType, TaskStatus, WriteStatus
from app.models import ApprovalTask
from app.services import log_service
from app.tools import list_pending_contract_approvals


def pull_and_dedupe(db: Session, limit: int = 20) -> dict:
    items = list_pending_contract_approvals(limit)
    created = updated = skipped = 0

    for it in items:
        code = it.get("approval_code")
        if not code:
            continue
        existing = db.query(ApprovalTask).filter(ApprovalTask.approval_code == code).first()
        if existing:
            if existing.task_status == TaskStatus.DONE:
                skipped += 1
                continue
            existing.approval_title = it.get("approval_title") or existing.approval_title
            existing.applicant_name = it.get("applicant_name") or existing.applicant_name
            db.commit()
            log_service.log(db, existing.id, LogLevel.INFO, LogType.FETCH, f"去重更新审批单 {code}")
            updated += 1
        else:
            task = ApprovalTask(
                approval_code=code,
                approval_title=it.get("approval_title", ""),
                applicant_name=it.get("applicant_name", ""),
                task_status=TaskStatus.PENDING,
                write_status=WriteStatus.NOT_WRITTEN,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            log_service.log(db, task.id, LogLevel.INFO, LogType.FETCH, f"新建审批任务 {code}")
            created += 1

    return {
        "pulled": len(items),
        "created": created,
        "updated": updated,
        "skipped": skipped,
    }
