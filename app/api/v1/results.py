from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import response
from app.core.database import get_db
from app.schemas.review import (
    CommentRequest,
    ReviewRequest,
    ReviewResultOut,
    SaveResultRequest,
)
from app.services import comment_service, rule_service

router = APIRouter()


@router.post("/tasks/{task_id}/review")
def review(task_id: int, body: ReviewRequest, db: Session = Depends(get_db)):
    """执行规则审查并返回命中结果和风险结论。"""
    return response.success(rule_service.review_task(db, task_id))


@router.get("/tasks/{task_id}/hits")
def hits(task_id: int, db: Session = Depends(get_db)):
    return response.success(rule_service.list_hits(db, task_id))


@router.get("/tasks/{task_id}/result")
def get_result(task_id: int, db: Session = Depends(get_db)):
    r = comment_service.get_result(db, task_id)
    if not r:
        return response.success(None)
    return response.success(ReviewResultOut.model_validate(r).model_dump())


@router.post("/tasks/{task_id}/result")
def save_result(task_id: int, body: SaveResultRequest, db: Session = Depends(get_db)):
    """保存审查结果。"""
    return response.success(comment_service.save_result(db, task_id, body))


@router.post("/tasks/{task_id}/comment")
def comment(task_id: int, body: CommentRequest, db: Session = Depends(get_db)):
    """将审查意见写回审批评论区。"""
    return response.success(comment_service.write(db, task_id, body.instance_id, body.review_id))
