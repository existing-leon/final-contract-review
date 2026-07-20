from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ReviewRequest(BaseModel):
    case_id: int


class HitItem(BaseModel):
    rule_code: str
    rule_name: str
    risk_level: str
    evidence_text: Optional[str] = None
    evidence_position: Optional[str] = None
    suggestion_text: Optional[str] = None
    hit_status: str = "hit"


class ReviewConclusion(BaseModel):
    task_id: int
    overall_risk_level: str
    hits: list[HitItem] = []
    focus_points: list[str] = []
    summary_text: str = ""


class SaveResultRequest(BaseModel):
    case_id: int
    overall_risk_level: str
    summary_text: str
    focus_points_json: list[Any] = []
    comment_text: str


class SaveResultResponse(BaseModel):
    review_id: int
    task_id: int
    saved_at: str


class CommentRequest(BaseModel):
    instance_id: str
    review_id: int


class CommentResult(BaseModel):
    task_id: int
    write_status: str
    write_response_text: Optional[str] = None
    comment_text: str


class ReviewResultOut(BaseModel):
    id: int
    task_id: int
    overall_risk_level: str
    summary_text: Optional[str] = None
    focus_points_json: list[Any] = []
    comment_text: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
