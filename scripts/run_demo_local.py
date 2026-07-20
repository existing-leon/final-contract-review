"""本地闭环演示：对 samples/ 中的真实 PDF 执行 解析 → 字段提取 → 规则匹配，打印命中结论。

不依赖 MySQL 与审批系统（规则取自 scripts/init_data.py 的内置 RULES）。

运行：
    pip install pdfplumber
    python scripts/run_demo_local.py
"""
import glob
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engine.field_extractor import extract_fields
from app.engine.parser import parse_file
from app.engine.rule_engine import match_rule, summarize_hits
from scripts.init_data import RULES

SAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples"
)


def _load_rules() -> list:
    return [SimpleNamespace(id=i, rule_status="enabled", **r) for i, r in enumerate(RULES)]


def demo(pdf_path: str, rules: list) -> None:
    print(f"\n{'=' * 60}\n📄 {os.path.basename(pdf_path)}\n{'=' * 60}")
    parsed = parse_file(pdf_path)  # pdfplumber 解析真实 PDF
    basic, clause, snippets = extract_fields(parsed)
    basic["_full_text"] = parsed["text"]
    ctx = {"basic_info": basic, "clause_info": clause}

    hits = []
    for rule in rules:
        ok, evidence, position = match_rule(rule, ctx)
        if ok:
            hits.append(
                {
                    "rule_code": rule.rule_code,
                    "rule_name": rule.rule_name,
                    "risk_level": rule.risk_level,
                    "evidence_text": evidence,
                    "evidence_position": position,
                    "suggestion_text": rule.suggestion_text,
                    "hit_status": "hit",
                }
            )

    overall, focus_points, summary = summarize_hits(hits)

    print(f"合同编号：{basic['contract_no']['value'] or '(未提取)'}")
    print(f"甲方：{basic['party_a']['value'] or '(未提取)'}    乙方：{basic['party_b']['value'] or '(未提取)'}")
    print(f"金额：{basic['amount']['value'] or '(未提取)'}    币种：{basic['currency']['value'] or '(未提取)'}")
    print(f"\n【总风险等级】{overall}")
    print(f"【摘要】{summary}")
    print("【命中规则】")
    if not hits:
        print("  （无）")
    for h in hits:
        print(f"  - [{h['risk_level']}] {h['rule_name']}：{(h['evidence_text'] or '').strip()}")
        print(f"      建议：{h['suggestion_text']}")


def main() -> None:
    pdfs = sorted(glob.glob(os.path.join(SAMPLES_DIR, "*.pdf")))
    if not pdfs:
        print("samples/ 下未找到 PDF。请先运行：python scripts/make_sample_pdf.py")
        return
    rules = _load_rules()
    for p in pdfs:
        demo(p, rules)
    print("\n✅ 本地演示完成。")


if __name__ == "__main__":
    main()
