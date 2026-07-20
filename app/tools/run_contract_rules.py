"""规则审查工具：对解析结果执行规则匹配，输出风险等级、命中证据和处理建议。"""
from typing import Any

from app.core.constants import HitStatus, RuleStatus
from app.core.database import SessionLocal
from app.engine.rule_engine import match_rule, summarize_hits
from app.models import ContractParse, ReviewRule


def run_contract_rules(case_id: int, db=None) -> dict[str, Any]:
    """case_id 即 task_id。读取解析结果，遍历启用规则，返回命中结论（不落库）。"""
    own = db is None
    db = db or SessionLocal()
    try:
        parse = db.query(ContractParse).filter(ContractParse.task_id == case_id).first()
        if not parse:
            return {
                "task_id": case_id,
                "overall_risk_level": "low",
                "hits": [],
                "focus_points": ["未找到解析结果，无法执行规则审查"],
                "summary_text": "未找到解析结果。",
            }

        parsed = {
            "basic_info": parse.basic_info_json or {},
            "clause_info": parse.clause_info_json or {},
        }
        rules = db.query(ReviewRule).filter(ReviewRule.rule_status == RuleStatus.ENABLED).all()

        hits: list[dict[str, Any]] = []
        for rule in rules:
            hit, evidence, position = match_rule(rule, parsed)
            if hit:
                hits.append(
                    {
                        "rule_id": rule.id,
                        "rule_code": rule.rule_code,
                        "rule_name": rule.rule_name,
                        "risk_level": rule.risk_level,
                        "evidence_text": evidence,
                        "evidence_position": position or "",
                        "suggestion_text": rule.suggestion_text or "",
                        "hit_status": HitStatus.HIT,
                    }
                )

        overall, focus_points, summary = summarize_hits(hits)
        return {
            "task_id": case_id,
            "overall_risk_level": overall,
            "hits": hits,
            "focus_points": focus_points,
            "summary_text": summary,
        }
    finally:
        if own:
            db.close()
