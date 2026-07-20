"""图片扫描件 OCR（百度 PaddleOCR）。

优先级：
1. PaddleOCR **PP-Structure 版面分析**（区分标题/正文/表格，尽量还原表格）—— settings.OCR_USE_LAYOUT=True
2. PaddleOCR **PP-OCRv4 纯文字识别**
3. RapidOCR(onnxruntime) 轻量回退

所有第三方库在函数内部 import，未安装时抛出明确的 BizException(OCR_FAILED)，
保证本模块自身 import 不依赖这些库。

兼容 paddleocr 2.6~2.7 系列 API；不同版本字段略有差异，已做容错。
"""
import re

from app.core.config import settings
from app.core.constants import ParseStatus
from app.core.exceptions import BizException, Errors
from app.core.logger import logger


def parse_image(file_path: str) -> dict:
    # 1. PP-Structure 版面分析
    if getattr(settings, "OCR_USE_LAYOUT", True):
        try:
            return _parse_with_ppstructure(file_path)
        except ImportError:
            pass  # 未安装 paddleocr，去试别的
        except BizException:
            raise  # 识别到但无文字，直接抛
        except Exception as e:
            logger.warning(f"PP-Structure 版面分析失败，降级为纯文字识别: {e}")

    # 2. PaddleOCR 纯文字识别
    try:
        return _parse_with_paddleocr(file_path)
    except ImportError:
        pass
    except BizException:
        raise

    # 3. RapidOCR 回退
    try:
        return _parse_with_rapidocr(file_path)
    except ImportError as e:
        raise BizException(
            *Errors.OCR_FAILED,
            data={"reason": "未安装 OCR 库（paddleocr 或 rapidocr-onnxruntime）"},
        ) from e


def _empty_result() -> dict:
    return {"text": "", "pages": [{"page": 1, "text": ""}],
            "tables": [], "parse_status": ParseStatus.FAILED, "parse_error": None}


def _finalize(text: str, tables: list[str] | None = None) -> dict:
    full = (text or "").strip()
    if not full:
        raise BizException(*Errors.OCR_FAILED, data={"reason": "OCR 未识别到文字"})
    return {
        "text": full,
        "pages": [{"page": 1, "text": full}],
        "tables": tables or [],
        "parse_status": ParseStatus.SUCCESS,
        "parse_error": None,
    }


def _extract_texts_from_res(res) -> list[str]:
    """从 PP-Structure / PaddleOCR 的 res 结构中尽量抽出文本行，兼容多种返回形态。"""
    out: list[str] = []
    if not res:
        return out
    if isinstance(res, list):
        for item in res:
            try:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    t = item[1]
                    if isinstance(t, (list, tuple)) and t:
                        out.append(str(t[0]))
                    elif t:
                        out.append(str(t))
                elif isinstance(item, str):
                    out.append(item)
            except Exception:
                continue
    elif isinstance(res, dict):
        # 表格区域可能是 {'cells': [...], 'html': '...'} 等
        html = res.get("html")
        if html:
            out.extend(_html_table_to_lines(html))
        for v in res.values():
            if isinstance(v, str) and v.strip():
                out.append(v)
    return out


def _html_table_to_lines(html_str: str) -> list[str]:
    """把 PP-Structure 表格的 html 粗略转成『单元格 | 单元格』文本行。"""
    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", html_str, re.S | re.I)
    cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
    cells = [c for c in cells if c]
    return [" | ".join(cells)] if cells else []


def _parse_with_ppstructure(file_path: str) -> dict:
    from paddleocr import PPStructure

    engine = PPStructure(show_log=False, layout=True, table=True, ocr=True, lang="ch")
    result = engine(file_path)

    titles: list[str] = []
    bodies: list[str] = []
    tables: list[str] = []
    for region in result or []:
        rtype = region.get("type") if isinstance(region, dict) else None
        region_texts = _extract_texts_from_res(region.get("res") if isinstance(region, dict) else None)
        if rtype == "title":
            titles.extend(region_texts)
        elif rtype == "table":
            # 表格区域单独保留还原文本
            table_text = _extract_texts_from_res(region) or region_texts
            if table_text:
                tables.append("\n".join(table_text))
            tables_lines = region_texts
            bodies.extend(tables_lines)
        else:  # text / list / figure 等
            bodies.extend(region_texts)

    full = "\n".join([*titles, *bodies])
    return _finalize(full, tables)


def _parse_with_paddleocr(file_path: str) -> dict:
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    result = ocr.ocr(file_path, cls=True)
    lines: list[str] = []
    for page in result or []:
        for line in page or []:
            if line and len(line) >= 2:
                t = line[1]
                if isinstance(t, (list, tuple)) and t:
                    lines.append(str(t[0]))
                elif t:
                    lines.append(str(t))
    return _finalize("\n".join(lines))


def _parse_with_rapidocr(file_path: str) -> dict:
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    result, _elapsed = engine(file_path)
    lines = [item[1] for item in (result or [])]
    return _finalize("\n".join(lines))
