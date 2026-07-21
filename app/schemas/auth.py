from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LoginResult(BaseModel):
    token: str
    user: UserOut
