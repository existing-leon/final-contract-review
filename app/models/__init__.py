"""ORM 模型聚合导出。导入本包即触发所有模型注册到 Base.metadata。"""
from app.models.approval_attachment import ApprovalAttachment
from app.models.approval_task import ApprovalTask
from app.models.comment_log import CommentLog
from app.models.contract_parse import ContractParse
from app.models.review_result import ReviewResult
from app.models.review_rule import ReviewRule
from app.models.rule_hit import RuleHit
from app.models.task_log import TaskLog
from app.models.user import User

__all__ = [
    "ApprovalTask",
    "ApprovalAttachment",
    "ContractParse",
    "ReviewRule",
    "RuleHit",
    "ReviewResult",
    "CommentLog",
    "TaskLog",
    "User",
]
