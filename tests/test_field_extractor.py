"""字段提取器测试。"""
from app.engine.field_extractor import extract_fields

TEXT = """采购合同
合同编号：HT-2026-001
甲方：示例科技有限公司
乙方：供应商有限公司
合同金额：500000 元，币种：人民币
预付款比例：40%
付款周期：90 天
生效时间：2026-08-01，到期时间：2027-07-31
本合同包含自动续约条款。
争议解决：由乙方所在地法院管辖。
"""

PARSED = {"text": TEXT, "pages": [{"page": 1, "text": TEXT}]}


def test_extract_basic_info():
    basic, _, _ = extract_fields(PARSED)
    assert basic["contract_no"]["value"] == "HT-2026-001"
    assert basic["party_a"]["value"] == "示例科技有限公司"
    assert basic["party_b"]["value"] == "供应商有限公司"
    assert basic["amount"]["value"] == "500000"
    assert basic["currency"]["value"] == "人民币"
    assert basic["effective_date"]["value"] == "2026-08-01"
    assert basic["expire_date"]["value"] == "2027-07-31"


def test_extract_clause_info():
    _, clause, _ = extract_fields(PARSED)
    assert clause["payment"]["extract_status"] == "success"
    assert clause["dispute"]["extract_status"] == "success"
    # 文本中不含验收条款
    assert clause["acceptance"]["extract_status"] == "failed"


def test_extract_snippets():
    _, _, snippets = extract_fields(PARSED)
    assert len(snippets) > 0
