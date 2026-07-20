"""规则匹配引擎。

支持四种 match_mode：
- keyword  : 关键词命中（match_text 以 | 分隔多关键词，任一命中即命中）
- regex    : 正则命中
- threshold: 阈值命中（match_text 形如 `<含一个捕获组的正则> > <数值>`，提取数值并比较）
- absence  : 缺失命中（match_text 为字段路径，对应值为空即命中）
"""
import re
from typing import Any

from app.core.constants import HitStatus, MatchMode, RiskLevel

_CONTEXT_PADDING = 40  # 命中证据上下文字符数


def _build_corpus(parsed: dict[str, Any]) -> str:
    """从 basic_info/clause_info 拼出全文用于关键词/正则匹配。"""
    parts: list[str] = []
    # 优先放入合同原文（解析时注入到 basic_info._full_text），保证 keyword/regex/threshold 全文命中
    full_text = (parsed.get("basic_info") or {}).get("_full_text")
    if full_text:
        parts.append(str(full_text))
    for section in ("basic_info", "clause_info"):
        section_data = parsed.get(section) or {}
        for key, field in section_data.items():
            if isinstance(field, dict):
                snippet = field.get("value") or field.get("snippet") or ""
            else:
                snippet = str(field)
            if snippet:
                parts.append(f"[{key}] {snippet}")
    return "\n".join(parts)


def _lookup_field(parsed: dict[str, Any], path: str) -> Any:
    """支持 'amount' 或 'clause.confidentiality' 形式的字段路径查找。"""
    if "." in path:
        section, key = path.split(".", 1)
        section = "clause_info" if section == "clause" else "basic_info"
        return (parsed.get(section) or {}).get(key)
    field = (parsed.get("basic_info") or {}).get(path)
    if field is None:
        field = (parsed.get("clause_info") or {}).get(path)
    return field


def _field_value(parsed: dict[str, Any], path: str) -> str:
    field = _lookup_field(parsed, path)
    if isinstance(field, dict):
        return str(field.get("value") or "").strip()
    return str(field or "").strip() if field else ""


def _snippet_around(corpus: str, start: int, end: int) -> str:
    s = max(0, start - _CONTEXT_PADDING)
    e = min(len(corpus), end + _CONTEXT_PADDING)
    snippet = corpus[s:e].replace("\n", " ").strip()
    return f"...{snippet}..."


def match_rule(rule, parsed: dict[str, Any]) -> tuple[bool, str | None, str | None]:
    """对单条规则执行匹配，返回 (是否命中, 证据片段, 位置)。"""
    mode = rule.match_mode
    text = rule.match_text or ""
    corpus = _build_corpus(parsed)

    if mode == MatchMode.KEYWORD:
        keywords = [k.strip() for k in text.split("|") if k.strip()]
        for kw in keywords:
            idx = corpus.find(kw)
            if idx >= 0:
                return True, _snippet_around(corpus, idx, idx + len(kw)), ""
        return False, None, None

    if mode == MatchMode.REGEX:
        try:
            m = re.search(text, corpus)
        except re.error:
            return False, None, None
        if m:
            return True, _snippet_around(corpus, m.start(), m.end()), ""
        return False, None, None

    if mode == MatchMode.THRESHOLD:
        # 形如：预付款\D{0,5}(\d{1,3})\s*% > 30
        for op in (">=", "<=", ">", "<"):
            if op in text:
                left, right = text.split(op, 1)
                try:
                    threshold = float(right.strip())
                    m = re.search(left.strip(), corpus)
                except (ValueError, re.error):
                    return False, None, None
                if not m or not m.groups():
                    return False, None, None
                try:
                    num = float(m.group(1))
                except (ValueError, IndexError):
                    return False, None, None
                hit = (
                    (num > threshold and op == ">")
                    or (num >= threshold and op == ">=")
                    or (num < threshold and op == "<")
                    or (num <= threshold and op == "<=")
                )
                if hit:
                    return True, _snippet_around(corpus, m.start(), m.end()), ""
                return False, None, None
        return False, None, None

    if mode == MatchMode.ABSENCE:
        value = _field_value(parsed, text.strip())
        if not value:
            return True, f"字段缺失: {text.strip()}", ""
        return False, None, None

    return False, None, None


def summarize_hits(hits: list[dict[str, Any]]) -> tuple[str, list[str], str]:
    """汇总总风险等级 + 审批关注点 + 中文摘要。"""
    levels = [h.get("risk_level") for h in hits if h.get("risk_level")]
    overall = RiskLevel.highest(levels)

    focus_points: list[str] = []
    for h in hits:
        name = h.get("rule_name", "")
        if name:
            focus_points.append(
                f"{name}（{h.get('risk_level', '')}）：{h.get('suggestion_text', '')}"
            )

    if not hits:
        summary = "未命中任何审查规则，合同整体风险较低，建议常规审批。"
    else:
        names = "、".join(h.get("rule_name", "") for h in hits)
        summary = (
            f"本次审查共命中 {len(hits)} 条规则（{names}），"
            f"总风险等级为【{overall}】，请重点关注上述事项。"
        )
    return overall, focus_points, summary
