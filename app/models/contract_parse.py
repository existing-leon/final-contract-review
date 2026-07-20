from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.approval_task import ApprovalTask


class ContractParse(Base):
    __tablename__ = "contract_parses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("approval_tasks.id"), unique=True, index=True
    )
    basic_info_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, comment="合同基本信息")
    clause_info_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, comment="条款信息")
    parse_status: Mapped[str] = mapped_column(String(16), default="pending")
    parse_error: Mapped[Optional[str]] = mapped_column(Text, comment="解析失败原因")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["ApprovalTask"] = relationship(back_populates="parse")
