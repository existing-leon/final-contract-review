"""百度智能云·文字识别 OCR 客户端。

鉴权：API Key + Secret Key 换 access_token（内存缓存，提前 10 分钟刷新）。
能力：通用文字识别（general_basic）+ 表格文字识别（table）。

⚠️ 数据安全：调用本模块会把图片上传到百度云服务器。
   建议仅作为「自部署 OCR 模型就绪前」的过渡方案；
   自部署就绪后将 settings.OCR_PROVIDER 改回 "local" 即可，业务代码无需改动。
"""
import base64
import re
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import BizException, Errors
from app.core.logger import logger

_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
_token_cache: dict[str, Any] = {"value": None, "expires_at": 0.0}


def _client(**kwargs) -> httpx.Client:
    return httpx.Client(trust_env=settings.OCR_TRUST_ENV, **kwargs)


def get_access_token() -> str:
    if _token_cache["value"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["value"]
    if not (settings.BAIDU_OCR_API_KEY and settings.BAIDU_OCR_SECRET_KEY):
        raise BizException(
            *Errors.OCR_FAILED,
            data={"reason": "未配置 BAIDU_OCR_API_KEY / BAIDU_OCR_SECRET_KEY"},
        )
    params = {
        "grant_type": "client_credentials",
        "client_id": settings.BAIDU_OCR_API_KEY,
        "client_secret": settings.BAIDU_OCR_SECRET_KEY,
    }
    with _client(timeout=30.0) as client:
        resp = client.get(_TOKEN_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    if "access_token" not in data:
        raise BizException(*Errors.OCR_FAILED, data={"reason": f"获取 access_token 失败: {data}"})
    _token_cache["value"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + float(data.get("expires_in", 2592000)) - 600
    logger.info("百度 OCR access_token 已刷新")
    return data["access_token"]


def _to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def recognize_text(file_path: str) -> str:
    token = get_access_token()
    data = {"image": _to_base64(file_path), "language_type": "CHN_ENG"}
    with _client(timeout=60.0) as client:
        resp = client.post(
            settings.BAIDU_OCR_GENERAL_URL, params={"access_token": token}, data=data
        )
        resp.raise_for_status()
        result = resp.json()
    if "error_code" in result:
        raise BizException(
            *Errors.OCR_FAILED,
            data={"reason": f'{result.get("error_code")}: {result.get("error_msg")}'},
        )
    words = [w.get("words", "") for w in result.get("words_result", [])]
    return "\n".join(words)


def _html_table_to_lines(html: str) -> str:
    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", html, re.S | re.I)
    cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
    cells = [c for c in cells if c]
    return " | ".join(cells) if cells else ""


def recognize_table(file_path: str) -> str:
    """表格识别，返回还原后的表格文本；失败返回空串（不阻断主流程）。"""
    try:
        token = get_access_token()
        data = {"image": _to_base64(file_path)}
        with _client(timeout=60.0) as client:
            resp = client.post(
                settings.BAIDU_OCR_TABLE_URL, params={"access_token": token}, data=data
            )
            resp.raise_for_status()
            result = resp.json()
        if "error_code" in result:
            logger.warning(f"表格识别失败: {result.get('error_code')}: {result.get('error_msg')}")
            return ""
        lines = []
        for t in result.get("tables_result", []):
            html = t.get("table_body", "") or t.get("content", "")
            if html:
                lines.append(_html_table_to_lines(html))
        return "\n".join(line for line in lines if line)
    except Exception as e:
        logger.warning(f"表格识别异常，跳过: {e}")
        return ""


def recognize(file_path: str) -> tuple[str, list[str]]:
    """通用识别 + 表格识别，返回 (全文文本, 表格文本列表)。"""
    text = recognize_text(file_path)
    table_text = recognize_table(file_path)
    tables = [table_text] if table_text else []
    return text, tables
