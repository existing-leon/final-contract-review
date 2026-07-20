"""解析模块：编排 下载 -> 解析 -> 落库，并驱动任务状态机。"""
from typing import Any

from sqlalchemy.orm import Session

from app.core.constants import LogLevel, LogType, ParseStatus, TaskStatus
from app.core.exceptions import BizException
from app.engine.state_machine import can_transition
from app.models import ApprovalAttachment, ApprovalTask, ContractParse
from app.services import attachment_service, log_service
from app.tools import parse_contract_document


def _safe_to(db: Session, task: ApprovalTask, to_status: str) -> None:
    """容错状态迁移：相同状态直接跳过；合法迁移则更新。"""
    if task.task_status == to_status:
        return
    if can_transition(task.task_status, to_status):
        task.task_status = to_status
        db.commit()


def _save_parse(db: Session, task_id: int, parsed: dict[str, Any]) -> ContractParse:
    parse = db.query(ContractParse).filter(ContractParse.task_id == task_id).first()
    if parse:
        parse.basic_info_json = parsed.get("basic_info")
        parse.clause_info_json = parsed.get("clause_info")
        parse.parse_status = parsed.get("parse_status", ParseStatus.SUCCESS)
        parse.parse_error = parsed.get("parse_error")
    else:
        parse = ContractParse(
            task_id=task_id,
            basic_info_json=parsed.get("basic_info"),
            clause_info_json=parsed.get("clause_info"),
            parse_status=parsed.get("parse_status", ParseStatus.SUCCESS),
            parse_error=parsed.get("parse_error"),
        )
        db.add(parse)
    db.commit()
    db.refresh(parse)
    return parse


def get_parse(db: Session, task_id: int) -> ContractParse | None:
    return db.query(ContractParse).filter(ContractParse.task_id == task_id).first()


def run_parse(db: Session, task_id: int, document_id: int | None = None) -> dict[str, Any]:
    task = db.get(ApprovalTask, task_id)
    if not task:
        raise BizException(1002, "任务不存在")

    _safe_to(db, task, TaskStatus.PARSING)
    log_service.log(db, task_id, LogLevel.INFO, LogType.PARSE, "开始解析合同")

    try:
        if document_id:
            att = db.get(ApprovalAttachment, document_id)
        else:
            att = (
                db.query(ApprovalAttachment)
                .filter(ApprovalAttachment.task_id == task_id)
                .order_by(ApprovalAttachment.id.desc())
                .first()
            )

        if not att or not att.file_path:
            att = attachment_service.download_and_save(
                db, task_id, "A1", task.approval_code, file_name=f"{task.approval_code}.pdf"
            )

        parsed = parse_contract_document(att.id, db)
        _save_parse(db, task_id, parsed)
        _safe_to(db, task, TaskStatus.REVIEWING)
        log_service.log(
            db, task_id, LogLevel.INFO, LogType.PARSE,
            f"解析完成 status={parsed.get('parse_status')}",
        )
        return parsed
    except BizException as e:
        _safe_to(db, task, TaskStatus.BLOCKED)
        log_service.log(db, task_id, LogLevel.ERROR, LogType.PARSE, f"解析失败: {e.message}")
        raise
