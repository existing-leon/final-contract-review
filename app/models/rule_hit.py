from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_task import ApprovalTask
    from app.models.review_rule import ReviewRule


class RuleHit(Base):
    __tablename__ = "rule_hits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("approval_tasks.id"), index=True
    )
    rule_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("review_rules.id"), index=True
    )
    evidence_text: Mapped[Optional[str]] = mapped_column(Text, comment="命中证据原文片段")
    evidence_position: Mapped[Optional[str]] = mapped_column(String(128), comment="证据位置")
    hit_status: Mapped[str] = mapped_column(String(16), default="hit")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["ApprovalTask"] = relationship(back_populates="hits")
    rule: Mapped["ReviewRule"] = relationship(back_populates="hits")
