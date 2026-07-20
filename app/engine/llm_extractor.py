"""LLM 字段提取器 v2：增强条款抽取。

改进点：
1. 更强的 system prompt：详细字段定义 + 抽取规则 + 条款示例。
2. 条款结构升级：每个条款输出 {exists, content, key_params, value, snippet, page, extract_status}
   - exists     : 条款是否存在
   - content    : 条款完整内容（尽量完整摘录原文）
   - key_params : 关键参数对象，如 {"预付款比例":"40%","付款周期":"90天"}
   - value      : 一句话概述（向下兼容，rule_engine 用它判 absence）
3. 长文档：放宽到 50000 字符，并强调通读全文不遗漏条款。
4. 可观测性：返回 meta(method/model)，由 parse_contract_document 写入结果与日志，
   便于排查『到底用没用上 LLM』。

输出结构与 field_extractor.extract_fields 基本同构（value/snippet/page/extract_status 一致），
下游 rule_engine / save_parse / 前端无需改动。
"""
import json
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.logger import logger
from app.engine.field_extractor import extract_fields as _regex_extract

_BASIC_KEYS = [
    "contract_title",
    "contract_no",
    "party_a",
    "party_b",
    "amount",
    "currency",
    "effective_date",
    "expire_date",
]
_CLAUSE_KEYS = {
    "payment": "付款：预付款比例、付款周期、付款方式",
    "delivery": "交付：交付时间、交付方式",
    "acceptance": "验收：验收标准、验收周期",
    "breach": "违约：违约金比例、违约责任方",
    "confidentiality": "保密：保密期限",
    "data": "数据处理：数据用途、个人信息",
    "ip": "知识产权：权属归属",
    "dispute": "争议解决：管辖地、解决方式(诉讼/仲裁)",
}

_SYSTEM_PROMPT = (
    "你是专业的合同信息抽取引擎。从合同正文中精确抽取结构化信息，"
    "严格只输出一个 JSON 对象，不要任何解释、不要 markdown 代码块。\n\n"
    "【两种对象】\n"
    "1) basic_info 字段对象：{value, snippet, page, extract_status}\n"
    "2) clause_info 条款对象：{exists, content, key_params, value, snippet, page, extract_status}\n\n"
    "【字段对象字段含义】\n"
    "- value：字段值（字符串），未找到为 null\n"
    "- snippet：原文片段（原样摘录），未找到为 null\n"
    "- page：页码（整数，无法判断填 1）\n"
    "- extract_status：\"success\"（找到）或 \"failed\"（未找到）\n\n"
    "【条款对象字段含义（重点）】\n"
    "- exists：布尔，该条款是否存在（一句话提及也算存在）\n"
    "- content：条款完整内容，尽量完整摘录原文（不要只取几个字）\n"
    "- key_params：从该条款抽取的关键参数对象；没有具体参数时为 {}\n"
    "- value：条款的一句话概述；exists=false 时为 null\n"
    "- snippet：条款原文片段\n"
    "- extract_status：exists=true 时 \"success\"，否则 \"failed\"\n\n"
    "【basic_info 字段】\n"
    "contract_title(合同标题), contract_no(合同编号), party_a(甲方/签约主体), "
    "party_b(乙方/对方), amount(合同金额,纯数字字符串,去掉千分位与币种), "
    "currency(币种), effective_date(生效日期), expire_date(到期日期)\n\n"
    "【clause_info 条款与典型 key_params】\n"
    + "；".join(f"{k}（{v}）" for k, v in _CLAUSE_KEYS.items())
    + "\n\n【关键要求】\n"
    "- 务必通读全文，不遗漏后半部分条款；\n"
    "- 严格 JSON，键名与上述完全一致。\n\n"
    "【basic_info 输出示例】（值必须放在 value 字段里，不要直接写字符串）\n"
    "原文：\"合同编号：HT-2026-001，甲方：示例科技有限公司\"\n"
    '"contract_no": {"value": "HT-2026-001", "snippet": "合同编号：HT-2026-001", "page": 1, "extract_status": "success"}, '
    '"party_a": {"value": "示例科技有限公司", "snippet": "甲方：示例科技有限公司", "page": 1, "extract_status": "success"}\n\n'
    "【条款输出示例】\n"
    "原文：\"预付款比例：40%，付款周期：90天。\"\n"
    '"payment": {"exists": true, "content": "预付款比例40%，付款周期90天", '
    '"key_params": {"预付款比例": "40%", "付款周期": "90天"}, '
    '"value": "预付款40%、账期90天", "snippet": "预付款比例：40%，付款周期：90天。", '
    '"page": 1, "extract_status": "success"}'
)

_USER_TEMPLATE = (
    "合同正文：\n----\n{text}\n----\n"
    "请抽取并仅输出一个 JSON 对象，包含 basic_info（字段：{basic}）与 "
    "clause_info（字段：{clause}）。"
)


def _llm_enabled() -> bool:
    return bool(settings.LLM_BASE_URL and settings.LLM_API_KEY and settings.LLM_MODEL)


def _build_payload(text: str) -> dict:
    return {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _USER_TEMPLATE.format(
                text=text[:50000],
                basic=",".join(_BASIC_KEYS),
                clause=",".join(_CLAUSE_KEYS.keys()),
            )},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }


def _call_llm(text: str) -> dict:
    url = settings.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = _build_payload(text)
    # connect 单独设短，read 用整体超时；trust_env=False 忽略系统/环境代理直连
    timeout = httpx.Timeout(settings.LLM_TIMEOUT, connect=10.0)

    last_err: Exception | None = None
    for attempt in range(1, settings.LLM_MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=timeout, trust_env=settings.LLM_TRUST_ENV) as client:
                resp = client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            last_err = e
            logger.warning(
                f"LLM 调用失败(第 {attempt}/{settings.LLM_MAX_RETRIES} 次): "
                f"{type(e).__name__}: {e}"
            )
            if attempt < settings.LLM_MAX_RETRIES:
                time.sleep(1.5 * attempt)
    assert last_err is not None
    raise last_err


def _norm_field(f: Any) -> dict[str, Any]:
    """basic_info 字段规整。容错：LLM 可能直接返回字符串值而非字段对象。"""
    if isinstance(f, dict):
        value = f.get("value")
        snippet = f.get("snippet")
        page = f.get("page")
        status = f.get("extract_status") or ("success" if value else "failed")
        return {
            "value": value,
            "snippet": snippet,
            "page": str(page) if page not in (None, "") else "",
            "extract_status": status,
        }
    # 容错：LLM 直接返回了字符串/数字值（未包成对象）
    if f in (None, "", []):
        return {"value": None, "snippet": None, "page": "", "extract_status": "failed"}
    value = str(f)
    return {"value": value, "snippet": value, "page": "", "extract_status": "success"}


def _norm_clause(f: Any) -> dict[str, Any]:
    """clause_info 条款规整：含 exists/content/key_params，并保证 value/snippet 兼容。"""
    if not isinstance(f, dict):
        return {
            "exists": False, "content": None, "key_params": {},
            "value": None, "snippet": None, "page": "", "extract_status": "failed",
        }
    exists = bool(f.get("exists", False))
    content = f.get("content")
    key_params = f.get("key_params") or {}
    snippet = f.get("snippet") or content
    value = f.get("value") or content  # value 缺失则回退 content，保证存在时 rule_engine 不误判 absence
    page = f.get("page")
    status = f.get("extract_status") or ("success" if exists else "failed")
    return {
        "exists": exists,
        "content": content,
        "key_params": key_params if isinstance(key_params, dict) else {},
        "value": value,
        "snippet": snippet,
        "page": str(page) if page not in (None, "") else "",
        "extract_status": status,
    }


def _normalize(raw: dict) -> tuple[dict, dict]:
    basic = {k: _norm_field(((raw.get("basic_info") or {}).get(k)) or {}) for k in _BASIC_KEYS}
    clause = {k: _norm_clause(((raw.get("clause_info") or {}).get(k)) or {}) for k in _CLAUSE_KEYS}
    return basic, clause


def _build_snippets(basic: dict, clause: dict) -> list[dict]:
    snippets: list[dict] = []
    for section_name, section in (("basic_info", basic), ("clause_info", clause)):
        for key, field in section.items():
            snip = field.get("snippet") or field.get("content")
            if snip:
                snippets.append(
                    {
                        "section": section_name,
                        "field": key,
                        "text": snip,
                        "page": field.get("page", ""),
                    }
                )
    return snippets


def extract_smart(parsed: dict[str, Any]) -> tuple[dict, dict, list[dict], dict]:
    """统一入口：配置了 LLM 则用 LLM 抽取（失败回退正则）；否则直接正则。

    返回 (basic_info, clause_info, snippets, meta)。
    meta = {"method": "llm"|"regex", "model": ...}，用于诊断与展示。
    """
    if not _llm_enabled():
        logger.info("LLM 未配置，使用正则提取")
        basic, clause, snippets = _regex_extract(parsed)
        return basic, clause, snippets, {"method": "regex"}

    try:
        raw = _call_llm(parsed.get("text", ""))
        basic, clause = _normalize(raw)
        snippets = _build_snippets(basic, clause)
        logger.info(f"LLM 字段提取成功 model={settings.LLM_MODEL}")
        return basic, clause, snippets, {"method": "llm", "model": settings.LLM_MODEL}
    except Exception as e:
        logger.warning(f"LLM 提取失败，回退正则: {e}")
        basic, clause, snippets = _regex_extract(parsed)
        return basic, clause, snippets, {"method": "regex", "fallback_reason": str(e)}
