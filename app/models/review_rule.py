from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.rule_hit import RuleHit


class ReviewRule(Base):
    __tablename__ = "review_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="规则编码")
    rule_name: Mapped[str] = mapped_column(String(128), comment="规则名称")
    risk_level: Mapped[str] = mapped_column(String(16), default="medium", comment="风险等级")
    rule_status: Mapped[str] = mapped_column(String(16), default="enabled", comment="启用状态")
    match_mode: Mapped[str] = mapped_column(String(16), comment="匹配模式")
    match_text: Mapped[Optional[str]] = mapped_column(Text, comment="匹配文本/表达式")
    suggestion_text: Mapped[Optional[str]] = mapped_column(Text, comment="处理建议")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    hits: Mapped[list["RuleHit"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )
