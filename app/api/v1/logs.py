from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import response
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.schemas.log import TaskLogOut
from app.services import log_service

router = APIRouter()


@router.get("/tasks/{task_id}/logs")
def list_logs(
    task_id: int,
    log_level: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    items = log_service.list_logs(db, task_id, log_level)
    return response.success([TaskLogOut.model_validate(l).model_dump() for l in items])
