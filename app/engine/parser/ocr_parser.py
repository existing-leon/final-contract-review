"""图片扫描件 OCR。

按 settings.OCR_PROVIDER 路由：
- baidu_api: 百度智能云文字识别 API（过渡方案，数据上传百度云）
- local    : 百度飞桨 PaddleOCR 本地推理（默认，数据不出本机；推荐生产）

切换：改 settings.OCR_PROVIDER 即可，调用方无感。
结果中的 ocr_meta 记录实际使用的 provider，供上层写入 task_logs 审计。
"""
import re

from app.core.config import settings
from app.core.constants import ParseStatus
from app.core.exceptions import BizException, Errors
from app.core.logger import logger


def _ocr_file(file_path: str) -> tuple[str, list[str], str]:
    """统一 OCR 入口（单张图片），返回 (text, tables, provider)。"""
    provider = getattr(settings, "OCR_PROVIDER", "local")
    if provider == "baidu_api":
        text, tables = _parse_with_baidu(file_path)
    else:
        text, tables = _parse_with_local(file_path)
    return text, tables, provider


def parse_image(file_path: str) -> dict:
    """独立图片 OCR，返回与其它解析器一致的结构（含 ocr_meta）。"""
    text, tables, provider = _ocr_file(file_path)
    return _finalize(text, tables, provider=provider, source="image")


# ----------------------- baidu api ----------------------- #

def _parse_with_baidu(file_path: str) -> tuple[str, list[str]]:
    from app.engine.parser.baidu_ocr import recognize

    return recognize(file_path)


# ----------------------- local (PaddleOCR) ----------------------- #

def _parse_with_local(file_path: str) -> tuple[str, list[str]]:
    if getattr(settings, "OCR_USE_LAYOUT", True):
        try:
            return _local_ppstructure(file_path)
        except ImportError:
            pass
        except BizException:
            raise
        except Exception as e:
            logger.warning(f"PP-Structure 版面分析失败，降级纯识别: {e}")
    try:
        return _local_paddleocr(file_path)
    except ImportError:
        pass
    except BizException:
        raise
    try:
        return _local_rapidocr(file_path)
    except ImportError as e:
        raise BizException(
            *Errors.OCR_FAILED,
            data={"reason": "未安装 OCR 库（paddleocr 或 rapidocr-onnxruntime）"},
        ) from e


def _extract_texts_from_res(res) -> list[str]:
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
        html = res.get("html")
        if html:
            lines = _html_table_to_lines(html)
            if lines:
                out.append(lines)
        for v in res.values():
            if isinstance(v, str) and v.strip():
                out.append(v)
    return out


def _html_table_to_lines(html: str) -> str:
    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", html, re.S | re.I)
    cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
    cells = [c for c in cells if c]
    return " | ".join(cells) if cells else ""


def _local_ppstructure(file_path: str) -> tuple[str, list[str]]:
    from paddleocr import PPStructure

    engine = PPStructure(show_log=False, layout=True, table=True, ocr=True, lang="ch")
    result = engine(file_path)
    titles, bodies, tables = [], [], []
    for region in result or []:
        rtype = region.get("type") if isinstance(region, dict) else None
        region_texts = _extract_texts_from_res(region.get("res") if isinstance(region, dict) else None)
        if rtype == "title":
            titles.extend(region_texts)
        elif rtype == "table":
            table_text = _extract_texts_from_res(region) or region_texts
            if table_text:
                tables.append("\n".join(table_text))
            bodies.extend(region_texts)
        else:
            bodies.extend(region_texts)
    full = "\n".join([*titles, *bodies])
    _ensure_nonempty(full)
    return full, tables


def _local_paddleocr(file_path: str) -> tuple[str, list[str]]:
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
    full = "\n".join(lines)
    _ensure_nonempty(full)
    return full, []


def _local_rapidocr(file_path: str) -> tuple[str, list[str]]:
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    result, _elapsed = engine(file_path)
    lines = [item[1] for item in (result or [])]
    full = "\n".join(lines)
    _ensure_nonempty(full)
    return full, []


def _ensure_nonempty(text: str) -> None:
    if not (text or "").strip():
        raise BizException(*Errors.OCR_FAILED, data={"reason": "OCR 未识别到文字"})


def _finalize(
    text: str,
    tables: list[str] | None = None,
    provider: str | None = None,
    source: str = "image",
    page_count: int = 1,
) -> dict:
    full = (text or "").strip()
    if not full:
        raise BizException(*Errors.OCR_FAILED, data={"reason": "OCR 未识别到文字"})
    return {
        "text": full,
        "pages": [{"page": 1, "text": full}],
        "tables": tables or [],
        "parse_status": ParseStatus.SUCCESS,
        "parse_error": None,
        "ocr_meta": {
            "scanned": True,
            "provider": provider,
            "source": source,
            "page_count": page_count,
        },
    }
