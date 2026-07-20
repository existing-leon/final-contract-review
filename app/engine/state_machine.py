"""任务 / 回写状态机。集中管理合法迁移，非法迁移抛 InvalidStateTransition。"""
from app.core.constants import TaskStatus, WriteStatus
from app.core.exceptions import InvalidStateTransition

# 任务状态合法迁移
TASK_TRANSITIONS: dict[str, set[str]] = {
    TaskStatus.PENDING: {TaskStatus.PARSING},
    TaskStatus.PARSING: {TaskStatus.REVIEWING, TaskStatus.BLOCKED},
    TaskStatus.REVIEWING: {TaskStatus.DONE, TaskStatus.BLOCKED},
    TaskStatus.BLOCKED: {TaskStatus.PARSING, TaskStatus.REVIEWING},
    TaskStatus.DONE: set(),
}

# 回写状态合法迁移
WRITE_TRANSITIONS: dict[str, set[str]] = {
    WriteStatus.NOT_WRITTEN: {WriteStatus.WRITING},
    WriteStatus.WRITING: {WriteStatus.SUCCESS, WriteStatus.FAILED},
    WriteStatus.FAILED: {WriteStatus.WRITING},
    WriteStatus.SUCCESS: set(),
}


def can_transition(from_status: str, to_status: str) -> bool:
    return to_status in TASK_TRANSITIONS.get(from_status, set())


def transition(from_status: str, to_status: str) -> str:
    if not can_transition(from_status, to_status):
        raise InvalidStateTransition(f"不允许从 {from_status} 迁移到 {to_status}")
    return to_status


def can_write_transition(from_status: str, to_status: str) -> bool:
    return to_status in WRITE_TRANSITIONS.get(from_status, set())


def write_transition(from_status: str, to_status: str) -> str:
    if not can_write_transition(from_status, to_status):
        raise InvalidStateTransition(f"回写状态不允许从 {from_status} 迁移到 {to_status}")
    return to_status
