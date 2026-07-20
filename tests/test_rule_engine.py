"""规则匹配引擎测试。"""
from types import SimpleNamespace

from app.engine.rule_engine import match_rule, summarize_hits


def _rule(**kw):
    return SimpleNamespace(**kw)


def _parsed(text, fields=None):
    return {"basic_info": {"_full_text": text, **(fields or {})}, "clause_info": {}}


def test_keyword_hit():
    r = _rule(match_mode="keyword", match_text="自动续约|自动续期")
    hit, evidence, _ = match_rule(r, _parsed("本合同到期自动续期一年"))
    assert hit and "自动续期" in evidence


def test_keyword_miss():
    r = _rule(match_mode="keyword", match_text="违约金")
    assert not match_rule(r, _parsed("本合同无相关条款"))[0]


def test_regex_hit():
    r = _rule(match_mode="regex", match_text=r"管辖.*?法院")
    assert match_rule(r, _parsed("由乙方所在地法院管辖"))[0]


def test_threshold_hit():
    r = _rule(match_mode="threshold", match_text=r"预付款\D{0,5}(\d{1,3})\s*% > 30")
    assert match_rule(r, _parsed("预付款比例：45%"))[0]


def test_threshold_below_not_hit():
    r = _rule(match_mode="threshold", match_text=r"预付款\D{0,5}(\d{1,3})\s*% > 30")
    assert not match_rule(r, _parsed("预付款比例：20%"))[0]


def test_absence_hit_when_missing():
    r = _rule(match_mode="absence", match_text="amount")
    assert match_rule(r, _parsed("正文", {"amount": {"value": None}}))[0]


def test_absence_miss_when_present():
    r = _rule(match_mode="absence", match_text="amount")
    assert not match_rule(r, _parsed("正文", {"amount": {"value": "500000"}}))[0]


def test_summarize_takes_highest():
    hits = [
        {"risk_level": "high", "rule_name": "A", "suggestion_text": "x"},
        {"risk_level": "low", "rule_name": "B", "suggestion_text": "y"},
    ]
    overall, focus, summary = summarize_hits(hits)
    assert overall == "high"
    assert len(focus) == 2
    assert "2" in summary


def test_summarize_empty():
    overall, focus, _ = summarize_hits([])
    assert overall == "low"
    assert focus == []
