"""评论回写工具：将最终审查意见写回审批评论区，并返回回写结果。"""
from typing import Any

from app.core.constants import WriteStatus
from app.core.database import SessionLocal
from app.core.exceptions import BizException, Errors
from app.core.logger import logger
from app.models import ApprovalTask, CommentLog, ReviewResult
from app.services import approval_client


def write_approval_comment(instance_id: str, review_id: int, db=None) -> dict[str, Any]:
    own = db is None
    db = db or SessionLocal()
    try:
        result = db.get(ReviewResult, review_id)
        if not result:
            raise BizException(*Errors.NOT_FOUND, data={"review_id": review_id})

        comment_text = result.comment_text or result.summary_text or ""
        task = db.query(ApprovalTask).filter(ApprovalTask.id == result.task_id).first()
        if task:
            task.write_status = WriteStatus.WRITING
            db.commit()

        log = CommentLog(task_id=result.task_id, write_status=WriteStatus.WRITING)
        db.add(log)
        db.commit()

        try:
            resp = approval_client.write_comment(instance_id, comment_text)
            log.write_status = WriteStatus.SUCCESS
            log.write_response_text = str(resp)
            if task:
                task.write_status = WriteStatus.SUCCESS
            db.commit()
            return {
                "task_id": result.task_id,
                "write_status": WriteStatus.SUCCESS,
                "write_response_text": str(resp),
                "comment_text": comment_text,
            }
        except Exception as e:
            logger.warning(f"回写失败: {e}")
            log.write_status = WriteStatus.FAILED
            log.write_response_text = str(e)
            if task:
                task.write_status = WriteStatus.FAILED
            db.commit()
            raise BizException(*Errors.WRITE_FAILED, data={"reason": str(e)}) from e
    finally:
        if own:
            db.close()
