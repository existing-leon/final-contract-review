"""规则初始化数据（推荐方式，避免 SQL 反斜杠转义问题）。

运行：python scripts/init_data.py
幂等：已存在的 rule_code 会被跳过。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal  # noqa: E402
from app.models import ReviewRule  # noqa: E402

# 规则定义；正则使用 Python 原始字符串 r"..."，反斜杠无需二次转义
RULES = [
    {"rule_code": "R001", "rule_name": "预付款比例过高", "risk_level": "high",
     "match_mode": "threshold", "match_text": r"预付款\D{0,5}(\d{1,3})\s*% > 30",
     "suggestion_text": "预付款比例建议不超过 30%，降低提前付款资金风险。"},
    {"rule_code": "R002", "rule_name": "付款周期过长", "risk_level": "medium",
     "match_mode": "threshold", "match_text": r"付款.{0,6}?([0-9]{1,3})\s*天 > 60",
     "suggestion_text": "付款周期建议不超过 60 天，避免账期过长。"},
    {"rule_code": "R003", "rule_name": "自动续约", "risk_level": "high",
     "match_mode": "keyword", "match_text": "自动续约|自动续期|自动延续",
     "suggestion_text": "谨慎接受自动续约条款，建议改为到期人工确认。"},
    {"rule_code": "R004", "rule_name": "违约责任", "risk_level": "high",
     "match_mode": "keyword", "match_text": "违约金|违约责任",
     "suggestion_text": "核对违约责任是否对等、违约金比例是否合理。"},
    {"rule_code": "R005", "rule_name": "管辖地不利", "risk_level": "medium",
     "match_mode": "keyword", "match_text": "管辖|仲裁|诉讼",
     "suggestion_text": "确认管辖/仲裁地是否有利于本方。"},
    {"rule_code": "R006", "rule_name": "主体信息缺失", "risk_level": "high",
     "match_mode": "absence", "match_text": "party_a",
     "suggestion_text": "缺少签约主体信息，请补充甲方主体。"},
    {"rule_code": "R007", "rule_name": "金额缺失", "risk_level": "high",
     "match_mode": "absence", "match_text": "amount",
     "suggestion_text": "缺少合同金额，请补充金额信息。"},
    {"rule_code": "R008", "rule_name": "保密条款缺失", "risk_level": "high",
     "match_mode": "absence", "match_text": "clause.confidentiality",
     "suggestion_text": "缺少保密条款，建议补充保密义务约定。"},
    {"rule_code": "R009", "rule_name": "数据处理条款缺失", "risk_level": "medium",
     "match_mode": "absence", "match_text": "clause.data",
     "suggestion_text": "缺少数据处理条款，建议补充数据合规约定。"},
    {"rule_code": "R010", "rule_name": "知识产权条款缺失", "risk_level": "medium",
     "match_mode": "absence", "match_text": "clause.ip",
     "suggestion_text": "缺少知识产权条款，建议明确权属归属。"},
    {"rule_code": "R011", "rule_name": "验收标准缺失", "risk_level": "medium",
     "match_mode": "absence", "match_text": "clause.acceptance",
     "suggestion_text": "缺少验收标准条款，建议补充验收标准与流程。"},
]


def main() -> None:
    db = SessionLocal()
    try:
        created = 0
        for r in RULES:
            exists = db.query(ReviewRule).filter(ReviewRule.rule_code == r["rule_code"]).first()
            if exists:
                continue
            db.add(ReviewRule(rule_status="enabled", **r))
            created += 1
        db.commit()
        print(f"✅ 规则初始化完成：本次新增 {created} 条，总计 {len(RULES)} 条")
    finally:
        db.close()


if __name__ == "__main__":
    main()
