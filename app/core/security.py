"""认证安全：密码哈希、JWT 编解码、当前用户依赖、角色校验依赖。"""
from datetime import datetime, timedelta, timezone
from typing import Callable

import bcrypt
import jwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import BizException, Errors
from app.models import User


def hash_password(password: str) -> str:
    """bcrypt 哈希（密码截断到 72 字节，bcrypt 算法上限）。"""
    pwd = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """校验密码与哈希是否匹配。"""
    pwd = password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(pwd, password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """解析 Bearer token 并返回当前用户；失败抛未授权(1001)。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise BizException(*Errors.UNAUTHORIZED)
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = int(payload.get("sub", 0))
    except Exception:
        raise BizException(*Errors.UNAUTHORIZED)
    user = db.get(User, user_id)
    if not user:
        raise BizException(*Errors.UNAUTHORIZED)
    return user


def require_role(*roles: str) -> Callable[..., User]:
    """返回一个依赖：校验当前用户角色在 roles 内，否则抛无权访问(1004)。"""

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise BizException(*Errors.FORBIDDEN)
        return user

    return _checker
