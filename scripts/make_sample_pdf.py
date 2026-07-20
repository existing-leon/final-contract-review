"""生成真实可解析的中文示例合同 PDF（reportlab + 内置 STSong-Light CJK 字体）。

运行：
    pip install reportlab
    python scripts/make_sample_pdf.py

产出三份 PDF 到 samples/，分别覆盖：低风险、高风险、字段缺失场景。
pdfplumber 可正常提取其文本（含中文）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# 注册 reportlab 内置中文 CID 字体（无需额外字体文件）
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

SAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples"
)

CONTRACTS: list[tuple[str, str, list[str]]] = [
    (
        "正常采购合同.pdf",
        "采购合同",
        [
            "合同编号：HT-NORMAL-001",
            "甲方：示例科技有限公司",
            "乙方：诚信供应商有限公司",
            "合同金额：300000 元，币种：人民币",
            "预付款比例：20%",
            "付款周期：30 天",
            "交付时间：2026-09-30 前完成交付。",
            "验收标准：到货后 7 个工作日内完成验收，验收合格后支付尾款。",
            "违约责任：任一方违约应承担违约责任，违约金为合同金额的 5%。",
            "保密条款：双方对在本合同履行中知悉的对方商业秘密负有保密义务。",
            "数据处理：双方应遵守数据安全与个人信息保护相关法律法规。",
            "知识产权：本合同项下交付物的知识产权归甲方所有。",
            "争议解决：由甲方所在地人民法院管辖。",
            "生效时间：2026-08-01，到期时间：2027-07-31",
        ],
    ),
    (
        "高风险采购合同.pdf",
        "采购合同",
        [
            "合同编号：HT-RISK-001",
            "甲方：示例科技有限公司",
            "乙方：某未知名供应商",
            "合同金额：2000000 元，币种：人民币",
            "预付款比例：50%",
            "付款周期：120 天",
            "本合同到期自动续约一年，除非一方提前 30 天书面通知。",
            "违约金为合同金额的 20%，由甲方单方承担。",
            "争议解决：由乙方所在地法院管辖。",
            "生效时间：2026-08-01，到期时间：2027-07-31",
        ],
    ),
    (
        "简易合同.pdf",
        "简易采购合同",
        [
            "合同编号：HT-SIMPLE-001",
            "本合同为简易采购合同，双方协商一致达成如下条款。",
            "预付款比例：35%",
            "付款周期：75 天",
        ],
    ),
]


def build_pdf(file_name: str, title: str, lines: list[str]) -> str:
    path = os.path.join(SAMPLES_DIR, file_name)
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    h = ParagraphStyle("cn_h", parent=styles["Title"], fontName="STSong-Light", fontSize=16, leading=24)
    body = ParagraphStyle(
        "cn_b", parent=styles["Normal"], fontName="STSong-Light", fontSize=11, leading=20
    )

    story: list = [Paragraph(title, h), Spacer(1, 8 * mm)]
    for line in lines:
        story.append(Paragraph(line, body))
        story.append(Spacer(1, 3 * mm))
    doc.build(story)
    return path


def main() -> None:
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    for file_name, title, lines in CONTRACTS:
        path = build_pdf(file_name, title, lines)
        print(f"✅ 生成: {path}")
    print(f"\n共生成 {len(CONTRACTS)} 份示例 PDF，位于 samples/")


if __name__ == "__main__":
    main()
