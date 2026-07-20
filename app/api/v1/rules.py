from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import response
from app.core.database import get_db
from app.schemas.rule import RuleCreate, RuleOut, RuleStatusRequest, RuleUpdate
from app.services import rule_service

router = APIRouter()


@router.get("")
def list_rules(
    rule_status: str | None = None,
    risk_level: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    items = rule_service.list_rules(db, rule_status, risk_level, keyword)
    return response.success([RuleOut.model_validate(r).model_dump() for r in items])


@router.post("")
def create_rule(body: RuleCreate, db: Session = Depends(get_db)):
    rule = rule_service.create_rule(db, body)
    return response.success(RuleOut.model_validate(rule).model_dump())


@router.put("/{rule_id}")
def update_rule(rule_id: int, body: RuleUpdate, db: Session = Depends(get_db)):
    rule = rule_service.update_rule(db, rule_id, body)
    return response.success(RuleOut.model_validate(rule).model_dump())


@router.patch("/{rule_id}/status")
def toggle_rule(rule_id: int, body: RuleStatusRequest, db: Session = Depends(get_db)):
    rule = rule_service.toggle_rule(db, rule_id, body.rule_status)
    return response.success(RuleOut.model_validate(rule).model_dump())
