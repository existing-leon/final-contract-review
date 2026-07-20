"""PDF 转图片（PyMuPDF / fitz），用于扫描件 PDF 的 OCR 前置。

依赖：pip install pymupdf
"""
import tempfile

from app.core.exceptions import BizException, Errors


def pdf_to_images(pdf_path: str, dpi: int = 200) -> list[tuple[int, str]]:
    """把 PDF 每页渲染成 PNG 临时文件，返回 [(page_no, tmp_png_path), ...]。

    调用方负责删除返回的临时文件。
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise BizException(
            *Errors.OCR_FAILED,
            data={"reason": "扫描件 PDF 需要转图片，请安装 PyMuPDF：pip install pymupdf"},
        ) from e

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    results: list[tuple[int, str]] = []
    doc = fitz.open(pdf_path)
    try:
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix)
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            pix.save(tmp.name)
            results.append((i, tmp.name))
    finally:
        doc.close()
    return results
