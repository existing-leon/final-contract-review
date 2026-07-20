"""日志模块：全链路日志写入 task_logs。"""
from sqlalchemy.orm import Session

from app.core.constants import LogType
from app.models import TaskLog


def log(db: Session, task_id: int, level: str, log_type: str, content: str) -> TaskLog:
    entry = TaskLog(
        task_id=task_id,
        log_level=level,
        log_type=log_type,
        log_content=content,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_logs(db: Session, task_id: int, log_level: str | None = None) -> list[TaskLog]:
    q = db.query(TaskLog).filter(TaskLog.task_id == task_id)
    if log_level:
        q = q.filter(TaskLog.log_level == log_level)
    return q.order_by(TaskLog.id.desc()).all()
