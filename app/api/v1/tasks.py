from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core import response
from app.core.constants import TaskStatus
from app.core.database import get_db
from app.core.exceptions import BizException
from app.engine.state_machine import can_transition
from app.models import ApprovalTask
from app.schemas.approval import PullRequest
from app.schemas.task import RetryRequest, TaskOut
from app.services import fetch_service

router = APIRouter()


@router.post("/pull")
def pull(body: PullRequest, db: Session = Depends(get_db)):
    """拉取并按 approval_code 去重。"""
    return response.success(fetch_service.pull_and_dedupe(db, body.limit))


@router.get("")
def list_tasks(
    task_status: str | None = None,
    write_status: str | None = None,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(ApprovalTask)
    if task_status:
        q = q.filter(ApprovalTask.task_status == task_status)
    if write_status:
        q = q.filter(ApprovalTask.write_status == write_status)
    if keyword:
        q = q.filter(
            ApprovalTask.approval_code.contains(keyword)
            | ApprovalTask.approval_title.contains(keyword)
        )
    total = q.count()
    items = q.order_by(ApprovalTask.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return response.success(
        {
            "total": total,
            "items": [TaskOut.model_validate(t).model_dump() for t in items],
        }
    )


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(ApprovalTask, task_id)
    if not task:
        raise BizException(1002, "任务不存在")
    return response.success(TaskOut.model_validate(task).model_dump())


@router.post("/{task_id}/retry")
def retry(task_id: int, body: RetryRequest, db: Session = Depends(get_db)):
    task = db.get(ApprovalTask, task_id)
    if not task:
        raise BizException(1002, "任务不存在")
    if task.task_status != TaskStatus.BLOCKED:
        raise BizException(1000, "仅 blocked 状态可重试")
    to = TaskStatus.REVIEWING if body.resume_from == "reviewing" else TaskStatus.PARSING
    if can_transition(task.task_status, to):
        task.task_status = to
        db.commit()
    return response.success({"task_id": task_id, "task_status": task.task_status})
