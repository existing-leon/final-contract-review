from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_task import ApprovalTask


class TaskLog(Base):
    __tablename__ = "task_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("approval_tasks.id"), index=True
    )
    log_level: Mapped[str] = mapped_column(String(16), default="info", comment="日志级别")
    log_type: Mapped[str] = mapped_column(String(32), comment="日志类型")
    log_content: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["ApprovalTask"] = relationship(back_populates="logs")
