from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_attachment import ApprovalAttachment
    from app.models.comment_log import CommentLog
    from app.models.contract_parse import ContractParse
    from app.models.review_result import ReviewResult
    from app.models.rule_hit import RuleHit
    from app.models.task_log import TaskLog


class ApprovalTask(Base):
    __tablename__ = "approval_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    approval_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="审批编号(去重唯一键)")
    approval_title: Mapped[Optional[str]] = mapped_column(String(255), comment="审批标题")
    applicant_name: Mapped[Optional[str]] = mapped_column(String(64), comment="申请人")
    task_status: Mapped[str] = mapped_column(String(16), default="pending", index=True, comment="任务状态")
    write_status: Mapped[str] = mapped_column(String(16), default="not_written", comment="回写状态")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    attachments: Mapped[list["ApprovalAttachment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    parse: Mapped[Optional["ContractParse"]] = relationship(
        back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
    hits: Mapped[list["RuleHit"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    result: Mapped[Optional["ReviewResult"]] = relationship(
        back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
    comment_logs: Mapped[list["CommentLog"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    logs: Mapped[list["TaskLog"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
