"""PDF 正文解析（pdfplumber）。"""
from app.core.constants import ParseStatus
from app.core.exceptions import BizException, Errors


def parse_pdf(file_path: str) -> dict:
    try:
        import pdfplumber
    except ImportError as e:
        raise BizException(*Errors.OCR_FAILED, data={"reason": "未安装 pdfplumber"}) from e

    pages = []
    full_text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append({"page": i, "text": text})
                full_text_parts.append(text)
    except Exception as e:
        raise BizException(*Errors.OCR_FAILED, data={"reason": str(e)}) from e

    full_text = "\n".join(full_text_parts).strip()
    if not full_text:
        # 可能是扫描件 PDF（无文本层），交给 OCR 兜底
        raise BizException(*Errors.DOC_EMPTY, data={"reason": "PDF 无文本层，疑似扫描件"})

    return {"text": full_text, "pages": pages, "parse_status": ParseStatus.SUCCESS, "parse_error": None}
