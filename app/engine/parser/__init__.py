"""文档解析器：按文件类型路由到 文本 / PDF / Word / OCR 解析。

每个解析器在函数内部 import 对应第三方库，未安装时抛出明确的 BizException，
保证本模块自身 import 不依赖这些库。
"""
from pathlib import Path

from app.core.constants import ParseStatus
from app.core.exceptions import BizException, Errors

__all__ = ["parse_file"]


def parse_text(file_path: str) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
    except Exception as e:
        raise BizException(*Errors.OCR_FAILED, data={"reason": str(e)}) from e
    if not text:
        raise BizException(*Errors.DOC_EMPTY, data={"reason": "文档内容为空"})
    return {
        "text": text,
        "pages": [{"page": 1, "text": text}],
        "parse_status": ParseStatus.SUCCESS,
        "parse_error": None,
    }


def parse_file(file_path: str) -> dict:
    """根据扩展名路由解析器，返回 {text, pages, parse_status, parse_error}。"""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in (".txt", ".text"):
        return parse_text(str(path))

    if suffix == ".pdf":
        from app.engine.parser.pdf_parser import parse_pdf

        return parse_pdf(str(path))
    if suffix in (".doc", ".docx"):
        from app.engine.parser.docx_parser import parse_docx

        return parse_docx(str(path))
    if suffix in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
        from app.engine.parser.ocr_parser import parse_image

        return parse_image(str(path))

    raise BizException(*Errors.PARAM_ERROR, data={"reason": f"不支持的文件类型: {suffix}"})
