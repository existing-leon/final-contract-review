"""规则模块：规则维护 + 规则审查编排（命中落库、风险汇总、生成评论）。"""
from typing import Any

from sqlalchemy.orm import Session

from app.core.constants import HitStatus, LogLevel, LogType, RiskLevel, RuleStatus
from app.models import ReviewRule, RuleHit
from app.schemas.rule import RuleCreate, RuleUpdate
from app.services import comment_service, log_service
from app.tools import run_contract_rules, save_review_result


# ---------------- 规则维护 ---------------- #

def list_rules(
    db: Session,
    rule_status: str | None = None,
    risk_level: str | None = None,
    keyword: str | None = None,
) -> list[ReviewRule]:
    q = db.query(ReviewRule)
    if rule_status:
        q = q.filter(ReviewRule.rule_status == rule_status)
    if risk_level:
        q = q.filter(ReviewRule.risk_level == risk_level)
    if keyword:
        q = q.filter(ReviewRule.rule_name.contains(keyword) | ReviewRule.rule_code.contains(keyword))
    return q.order_by(ReviewRule.id.asc()).all()


def create_rule(db: Session, payload: RuleCreate) -> ReviewRule:
    rule = ReviewRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule_id: int, payload: RuleUpdate) -> ReviewRule:
    rule = db.get(ReviewRule, rule_id)
    if not rule:
        from app.core.exceptions import BizException

        raise BizException(1002, "规则不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule


def toggle_rule(db: Session, rule_id: int, rule_status: str) -> ReviewRule:
    rule = db.get(ReviewRule, rule_id)
    if not rule:
        from app.core.exceptions import BizException

        raise BizException(1002, "规则不存在")
    rule.rule_status = rule_status
    db.commit()
    db.refresh(rule)
    return rule


# ---------------- 规则审查 ---------------- #

def review_task(db: Session, task_id: int) -> dict[str, Any]:
    conclusion = run_contract_rules(task_id, db)

    # 清旧命中，落库新命中
    db.query(RuleHit).filter(RuleHit.task_id == task_id).delete()
    for h in conclusion["hits"]:
        db.add(
            RuleHit(
                task_id=task_id,
                rule_id=h.get("rule_id"),
                evidence_text=h.get("evidence_text"),
                evidence_position=h.get("evidence_position"),
                hit_status=HitStatus.HIT,
            )
        )
    db.commit()

    # 生成评论并保存审查结果
    comment_text = comment_service.build_comment_text(conclusion)
    save_review_result(
        case_id=task_id,
        overall_risk_level=conclusion["overall_risk_level"],
        summary_text=conclusion["summary_text"],
        focus_points_json=conclusion["focus_points"],
        comment_text=comment_text,
        db=db,
    )
    log_service.log(
        db, task_id, LogLevel.INFO, LogType.REVIEW,
        f"规则审查完成，命中 {len(conclusion['hits'])} 条，总风险 {conclusion['overall_risk_level']}",
    )
    conclusion["comment_text"] = comment_text
    return conclusion


def list_hits(db: Session, task_id: int) -> list[dict[str, Any]]:
    rows = (
        db.query(RuleHit, ReviewRule)
        .join(ReviewRule, RuleHit.rule_id == ReviewRule.id)
        .filter(RuleHit.task_id == task_id)
        .order_by(RuleHit.id.asc())
        .all()
    )
    return [
        {
            "rule_code": rule.rule_code,
            "rule_name": rule.rule_name,
            "risk_level": rule.risk_level,
            "evidence_text": hit.evidence_text,
            "evidence_position": hit.evidence_position,
            "suggestion_text": rule.suggestion_text,
            "hit_status": hit.hit_status,
        }
        for hit, rule in rows
    ]
