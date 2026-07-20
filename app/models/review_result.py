from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_task import ApprovalTask


class ReviewResult(Base):
    __tablename__ = "review_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("approval_tasks.id"), unique=True, index=True
    )
    overall_risk_level: Mapped[str] = mapped_column(String(16), comment="总风险等级")
    summary_text: Mapped[Optional[str]] = mapped_column(Text, comment="中文摘要")
    focus_points_json: Mapped[Optional[list[Any]]] = mapped_column(JSON, comment="审批关注点")
    comment_text: Mapped[Optional[str]] = mapped_column(Text, comment="回写内容")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["ApprovalTask"] = relationship(back_populates="result")
