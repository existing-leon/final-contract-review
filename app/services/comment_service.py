"""回写模块：生成评论内容、写回审批评论区、保存回写日志、驱动任务到 done。"""
from typing import Any

from sqlalchemy.orm import Session

from app.core.constants import LogLevel, LogType, TaskStatus
from app.core.exceptions import BizException
from app.engine.state_machine import can_transition
from app.models import ApprovalTask, ReviewResult
from app.schemas.review import SaveResultRequest
from app.services import log_service
from app.tools import save_review_result, write_approval_comment


def build_comment_text(conclusion: dict[str, Any]) -> str:
    """根据审查结论组装写入评论区的文本。"""
    lines: list[str] = []
    lines.append("【合同智能审查意见】")
    lines.append(f"总风险等级：{conclusion.get('overall_risk_level', '')}")
    lines.append("")
    lines.append(conclusion.get("summary_text", ""))

    focus = conclusion.get("focus_points") or []
    if focus:
        lines.append("")
        lines.append("审批关注点：")
        for i, fp in enumerate(focus, start=1):
            lines.append(f"{i}. {fp}")

    hits = conclusion.get("hits") or []
    if hits:
        lines.append("")
        lines.append("命中规则明细：")
        for h in hits:
            lines.append(
                f"- {h.get('rule_name')}（{h.get('risk_level')}）：{(h.get('evidence_text') or '').strip()}"
            )
            if h.get("suggestion_text"):
                lines.append(f"    建议：{h['suggestion_text']}")
    lines.append("")
    lines.append("（本意见由合同审批审查系统自动生成，仅供审批参考，最终决策由审批人确认。）")
    return "\n".join(lines)


def get_result(db: Session, task_id: int) -> ReviewResult | None:
    return db.query(ReviewResult).filter(ReviewResult.task_id == task_id).first()


def save_result(db: Session, task_id: int, payload: SaveResultRequest) -> dict[str, Any]:
    return save_review_result(
        case_id=task_id,
        overall_risk_level=payload.overall_risk_level,
        summary_text=payload.summary_text,
        focus_points_json=payload.focus_points_json,
        comment_text=payload.comment_text,
        db=db,
    )


def write(db: Session, task_id: int, instance_id: str, review_id: int) -> dict[str, Any]:
    task = db.get(ApprovalTask, task_id)
    if not task:
        raise BizException(1002, "任务不存在")

    try:
        result = write_approval_comment(instance_id, review_id, db)
        if can_transition(task.task_status, TaskStatus.DONE):
            task.task_status = TaskStatus.DONE
            db.commit()
        log_service.log(db, task_id, LogLevel.INFO, LogType.COMMENT, "评论回写成功")
        return result
    except BizException as e:
        if can_transition(task.task_status, TaskStatus.BLOCKED):
            task.task_status = TaskStatus.BLOCKED
            db.commit()
        log_service.log(db, task_id, LogLevel.ERROR, LogType.COMMENT, f"评论回写失败: {e.message}")
        raise
