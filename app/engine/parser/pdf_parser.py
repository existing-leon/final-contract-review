"""PDF 解析。

策略：
1) 文本型 PDF：pdfplumber 提取文本层（保持原有逻辑不变）。
2) 扫描件 PDF（无文本层）：PyMuPDF 转图片，逐页走 OCR（按 OCR_PROVIDER 路由）。

结果中的 ocr_meta 记录是否扫描件 / provider / 页数 / 来源，供上层审计。
"""
import os

from app.core.constants import ParseStatus
from app.core.exceptions import BizException, Errors
from app.core.logger import logger


def parse_pdf(file_path: str) -> dict:
    # 1) 文本层（文本型 PDF）
    pages: list[dict] = []
    parts: list[str] = []
    try:
        import pdfplumber

        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                t = page.extract_text() or ""
                pages.append({"page": i, "text": t})
                parts.append(t)
    except ImportError as e:
        raise BizException(*Errors.OCR_FAILED, data={"reason": "未安装 pdfplumber"}) from e
    except Exception as e:
        raise BizException(*Errors.OCR_FAILED, data={"reason": str(e)}) from e

    full = "\n".join(parts).strip()
    if full:
        return {
            "text": full,
            "pages": pages,
            "tables": [],
            "parse_status": ParseStatus.SUCCESS,
            "parse_error": None,
            "ocr_meta": {
                "scanned": False,
                "provider": None,
                "source": "text_pdf",
                "page_count": len(pages),
            },
        }

    # 2) 无文本层 → 扫描件：转图片 + OCR
    logger.info("PDF 无文本层，按扫描件处理：转图片后走 OCR")
    return _ocr_scanned_pdf(file_path)


def _ocr_scanned_pdf(pdf_path: str) -> dict:
    from app.engine.parser.ocr_parser import _ocr_file
    from app.engine.parser.pdf_to_image import pdf_to_images

    imgs = pdf_to_images(pdf_path)  # 失败会抛 OCR_FAILED 并提示装 pymupdf

    pages: list[dict] = []
    parts: list[str] = []
    tables: list[str] = []
    used_provider = "unknown"
    try:
        for page_no, img_path in imgs:
            text, tbls, provider = _ocr_file(img_path)
            pages.append({"page": page_no, "text": text})
            parts.append(text)
            tables.extend(tbls or [])
            used_provider = provider
    finally:
        for _, p in imgs:
            try:
                os.remove(p)
            except OSError:
                pass

    full = "\n".join(parts).strip()
    if not full:
        raise BizException(*Errors.OCR_FAILED, data={"reason": "扫描件 PDF OCR 未识别到文字"})
    return {
        "text": full,
        "pages": pages,
        "tables": tables,
        "parse_status": ParseStatus.SUCCESS,
        "parse_error": None,
        "ocr_meta": {
            "scanned": True,
            "provider": used_provider,
            "source": "scanned_pdf",
            "page_count": len(imgs),
        },
    }
