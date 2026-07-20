from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import response
from app.core.database import get_db
from app.schemas.parse import ParseRequest
from app.services import parse_service

router = APIRouter()


@router.post("/tasks/{task_id}/parse")
def parse(task_id: int, body: ParseRequest, db: Session = Depends(get_db)):
    """解析合同文档并返回结构化字段。"""
    return response.success(parse_service.run_parse(db, task_id, body.document_id))


@router.get("/tasks/{task_id}/parse")
def get_parse(task_id: int, db: Session = Depends(get_db)):
    p = parse_service.get_parse(db, task_id)
    if not p:
        return response.success(None)
    return response.success(
        {
            "task_id": task_id,
            "parse_status": p.parse_status,
            "basic_info": p.basic_info_json,
            "clause_info": p.clause_info_json,
            "parse_error": p.parse_error,
        }
    )
