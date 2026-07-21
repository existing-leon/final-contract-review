"""认证路由：登录、当前用户。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import response
from app.core.database import get_db
from app.core.exceptions import BizException, Errors
from app.core.security import create_access_token, get_current_user, verify_password
from app.models import User
from app.schemas.auth import LoginResult, UserLogin, UserOut

router = APIRouter()


@router.post("/login")
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise BizException(*Errors.UNAUTHORIZED)
    token = create_access_token(user.id, user.role)
    return response.success(
        LoginResult(token=token, user=UserOut.model_validate(user)).model_dump()
    )


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return response.success(UserOut.model_validate(current_user).model_dump())
