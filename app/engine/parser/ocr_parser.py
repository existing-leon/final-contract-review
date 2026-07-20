"""图片扫描件 OCR 解析。

优先使用 RapidOCR(onnxruntime)，回退 PaddleOCR。两者皆未安装时抛 OCR_FAILED。
"""
from app.core.constants import ParseStatus
from app.core.exceptions import BizException, Errors


def parse_image(file_path: str) -> dict:
    try:
        return _parse_with_rapidocr(file_path)
    except ImportError:
        pass
    try:
        return _parse_with_paddleocr(file_path)
    except ImportError as e:
        raise BizException(*Errors.OCR_FAILED, data={"reason": "未安装 OCR 库(rapidocr-onnxruntime / paddleocr)"}) from e


def _parse_with_rapidocr(file_path: str) -> dict:
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    result, _elapsed = engine(file_path)
    pages = []
    parts = []
    if result:
        lines = [item[1] for item in result]
        text = "\n".join(lines).strip()
        pages.append({"page": 1, "text": text})
        parts.append(text)
    full_text = "\n".join(parts).strip()
    if not full_text:
        raise BizException(*Errors.OCR_FAILED, data={"reason": "OCR 未识别到文字"})
    return {"text": full_text, "pages": pages, "parse_status": ParseStatus.SUCCESS, "parse_error": None}


def _parse_with_paddleocr(file_path: str) -> dict:
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    result = ocr.ocr(file_path, cls=True)
    parts = []
    if result and result[0]:
        for line in result[0]:
            if line and len(line) >= 2:
                parts.append(line[1][0])
    full_text = "\n".join(parts).strip()
    if not full_text:
        raise BizException(*Errors.OCR_FAILED, data={"reason": "OCR 未识别到文字"})
    return {
        "text": full_text,
        "pages": [{"page": 1, "text": full_text}],
        "parse_status": ParseStatus.SUCCESS,
        "parse_error": None,
    }
