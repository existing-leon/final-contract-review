"""结果保存工具：保存审查结果、命中规则和摘要信息。"""
from datetime import datetime
from typing import Any

from app.core.database import SessionLocal
from app.models import ReviewResult


def save_review_result(
    case_id: int,
    overall_risk_level: str,
    summary_text: str,
    focus_points_json: list[Any],
    comment_text: str,
    db=None,
) -> dict[str, Any]:
    """落库 review_results（存在则更新）。"""
    own = db is None
    db = db or SessionLocal()
    try:
        result = db.query(ReviewResult).filter(ReviewResult.task_id == case_id).first()
        if result:
            result.overall_risk_level = overall_risk_level
            result.summary_text = summary_text
            result.focus_points_json = focus_points_json
            result.comment_text = comment_text
        else:
            result = ReviewResult(
                task_id=case_id,
                overall_risk_level=overall_risk_level,
                summary_text=summary_text,
                focus_points_json=focus_points_json,
                comment_text=comment_text,
            )
            db.add(result)
        db.commit()
        db.refresh(result)
        return {
            "review_id": result.id,
            "task_id": case_id,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    finally:
        if own:
            db.close()
