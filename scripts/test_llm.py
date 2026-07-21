"""快速测试 LLM 字段抽取效果（验证模型是否生效 + 看条款抽取质量）。

用法：
    python scripts/test_llm.py                # 用内置示例文本
    python scripts/test_llm.py path/合同.txt  # 用指定文本文件

依赖后端环境变量（.env）中的 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.engine.llm_extractor import _llm_enabled, extract_smart  # noqa: E402

_SAMPLE = """采购合同
合同编号：HT-2026-DEMO-001
甲方：示例科技有限公司
乙方：某供应商有限公司
合同金额：2,000,000 元，币种：人民币
预付款比例：45%，付款周期：120 天，到货后 30 天内付清尾款。
交付时间：2026-09-30 前完成交付。
验收标准：到货后 7 个工作日内完成验收。
本合同到期自动续约一年，除非一方提前 30 天书面通知。
违约金为合同金额的 20%，由甲方单方承担。
争议解决：由乙方所在地人民法院管辖。
生效时间：2026-08-01，到期时间：2027-07-31
"""


def main() -> None:
    print("=" * 60)
    print("LLM 已配置 :", _llm_enabled())
    print("LLM_MODEL  :", settings.LLM_MODEL or "(空)")
    print("LLM_BASE_URL:", settings.LLM_BASE_URL or "(空)")
    print("=" * 60)

    text = _SAMPLE
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            text = f.read()

    parsed = {"text": text, "pages": [{"page": 1, "text": text}]}
    basic, clause, snippets, meta = extract_smart(parsed)

    print("\n提取方式:", meta)
    if meta.get("method") != "llm":
        print("⚠️  本次未走 LLM！若已配置 key，多半是模型名无效或接口报错。")
        print("   回退原因:", meta.get("fallback_reason"))

    print("\n--- basic_info ---")
    for k, v in basic.items():
        if k == "_full_text":
            continue
        print(f"  {k}: {v}")

    print("\n--- clause_info ---")
    for k, v in clause.items():
        print(f"  {k}: exists={v.get('exists')} status={v.get('extract_status')} "
              f"key_params={v.get('key_params')}")
        if v.get("content"):
            print(f"      content: {v.get('content')}")


if __name__ == "__main__":
    main()
