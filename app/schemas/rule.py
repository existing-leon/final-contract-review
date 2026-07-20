from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RuleCreate(BaseModel):
    rule_code: str
    rule_name: str
    risk_level: str
    rule_status: str = "enabled"
    match_mode: str
    match_text: str
    suggestion_text: str


class RuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    risk_level: Optional[str] = None
    rule_status: Optional[str] = None
    match_mode: Optional[str] = None
    match_text: Optional[str] = None
    suggestion_text: Optional[str] = None


class RuleStatusRequest(BaseModel):
    rule_status: str  # enabled / disabled


class RuleOut(BaseModel):
    id: int
    rule_code: str
    rule_name: str
    risk_level: str
    rule_status: str
    match_mode: str
    match_text: Optional[str] = None
    suggestion_text: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
