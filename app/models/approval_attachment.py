from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_task import ApprovalTask


class ApprovalAttachment(Base):
    __tablename__ = "approval_attachments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("approval_tasks.id"), index=True
    )
    file_name: Mapped[Optional[str]] = mapped_column(String(255))
    file_type: Mapped[Optional[str]] = mapped_column(String(32))
    file_path: Mapped[Optional[str]] = mapped_column(String(512))
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    checksum: Mapped[Optional[str]] = mapped_column(String(128))
    download_status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["ApprovalTask"] = relationship(back_populates="attachments")
