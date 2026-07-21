from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """系统登录用户（法务审核人 / 系统管理员）。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="登录用户名")
    password_hash: Mapped[str] = mapped_column(String(128), comment="密码哈希（bcrypt）")
    role: Mapped[str] = mapped_column(String(16), default="legal", comment="角色：admin/legal")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
