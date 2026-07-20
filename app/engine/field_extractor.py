"""合同字段提取器：从解析后的全文 + 分页，提取基本信息与条款信息。

每个字段输出为统一的「字段对象」：
{value, snippet, page, extract_status}
"""
import re
from typing import Any

from app.core.constants import ParseStatus

_PAD = 30


def _field(value: Any, snippet: str | None, page: Any, status: str = "success") -> dict[str, Any]:
    return {
        "value": value,
        "snippet": snippet,
        "page": str(page) if page is not None else "",
        "extract_status": status if value else "failed",
    }


def _search(pages: list[dict], pattern: str, flags: int = 0):
    """在分页中按顺序搜索，返回 (match, snippet, page_number)。"""
    for p in pages:
        m = re.search(pattern, p.get("text", ""), flags)
        if m:
            text = p.get("text", "")
            s = max(0, m.start() - _PAD)
            e = min(len(text), m.end() + _PAD)
            return m, text[s:e].replace("\n", " ").strip(), p.get("page")
    return None, None, None


def _find_clause(pages: list[dict], keywords: list[str]) -> dict[str, Any]:
    pattern = "|".join(re.escape(k) for k in keywords)
    m, snippet, page = _search(pages, pattern)
    return _field(snippet, snippet, page, ParseStatus.SUCCESS if m else "failed")


def extract_basic_info(pages: list[dict]) -> dict[str, dict[str, Any]]:
    info: dict[str, dict[str, Any]] = {}

    # 合同标题：首个含「合同」的非空行
    title = ""
    for p in pages:
        for line in (p.get("text") or "").splitlines():
            if line.strip() and "合同" in line:
                title = line.strip()
                break
        if title:
            break
    info["contract_title"] = _field(title, title, 1, "success" if title else "failed")

    m, sn, pg = _search(pages, r"合同编号[:：]?\s*([A-Za-z0-9\-_/]+)")
    info["contract_no"] = _field(m.group(1) if m else None, sn, pg)

    m, sn, pg = _search(pages, r"甲方[:：]\s*(.+?)(?:\n|$)")
    info["party_a"] = _field((m.group(1).strip() if m else None), sn, pg)

    m, sn, pg = _search(pages, r"乙方[:：]\s*(.+?)(?:\n|$)")
    info["party_b"] = _field((m.group(1).strip() if m else None), sn, pg)

    m, sn, pg = _search(pages, r"(?:合同)?金额[:：]?\s*([\d,，.]+)\s*(?:元|人民币)?")
    info["amount"] = _field((m.group(1).replace(",", "").replace("，", "") if m else None), sn, pg)

    m, sn, pg = _search(pages, r"币种[:：]\s*(\S+)")
    currency = m.group(1).strip() if m else ("人民币" if "人民币" in (pages[0].get("text") if pages else "") else None)
    info["currency"] = _field(currency, sn, pg)

    m, sn, pg = _search(pages, r"生效(?:时间|日期)?[:：]\s*([\d\-/年月日]+)")
    info["effective_date"] = _field((m.group(1).strip() if m else None), sn, pg)

    m, sn, pg = _search(pages, r"(?:到期|终止)(?:时间|日期)?[:：]\s*([\d\-/年月日]+)")
    info["expire_date"] = _field((m.group(1).strip() if m else None), sn, pg)

    return info


def extract_clause_info(pages: list[dict]) -> dict[str, dict[str, Any]]:
    return {
        "payment": _find_clause(pages, ["付款", "预付款", "付款周期", "支付方式"]),
        "delivery": _find_clause(pages, ["交付", "交货", "发货"]),
        "acceptance": _find_clause(pages, ["验收", "验收标准"]),
        "breach": _find_clause(pages, ["违约", "违约金", "违约责任"]),
        "confidentiality": _find_clause(pages, ["保密", "保密义务"]),
        "data": _find_clause(pages, ["数据", "数据处理", "个人信息"]),
        "ip": _find_clause(pages, ["知识产权", "专利", "著作权", "商标"]),
        "dispute": _find_clause(pages, ["争议", "管辖", "仲裁", "诉讼"]),
    }


def extract_fields(parsed: dict[str, Any]) -> tuple[dict, dict, list[dict]]:
    """返回 (basic_info, clause_info, snippets)。"""
    pages = parsed.get("pages") or [{"page": 1, "text": parsed.get("text", "")}]
    basic = extract_basic_info(pages)
    clause = extract_clause_info(pages)

    snippets: list[dict[str, Any]] = []
    for section_name, section in (("basic_info", basic), ("clause_info", clause)):
        for key, field in section.items():
            if field.get("snippet"):
                snippets.append(
                    {"section": section_name, "field": key, "text": field["snippet"], "page": field["page"]}
                )
    return basic, clause, snippets
