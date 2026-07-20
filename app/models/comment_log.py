from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_task import ApprovalTask


class CommentLog(Base):
    __tablename__ = "comment_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("approval_tasks.id"), index=True
    )
    write_status: Mapped[str] = mapped_column(String(16), default="not_written")
    write_response_text: Mapped[Optional[str]] = mapped_column(Text, comment="回写响应")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["ApprovalTask"] = relationship(back_populates="comment_logs")
