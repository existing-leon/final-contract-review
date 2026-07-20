"""审批系统对接客户端。

- settings.MOCK_APPROVAL=True：返回 mock 数据，开箱可演示闭环。
  mock 附件优先取 samples/ 下**真实 PDF**（让 pdfplumber 解析真实文档）；
  若 samples 无 PDF 且未安装 reportlab，则回退为内置纯文本。
- settings.MOCK_APPROVAL=False：通过 HTTPX 调用真实审批系统接口。
"""
import hashlib
import uuid
import zlib
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import BizException, Errors
from app.core.logger import logger


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.APPROVAL_API_KEY}",
        "Content-Type": "application/json",
    }


# ----------------------- 路径与示例 PDF ----------------------- #

def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _samples_dir() -> Path:
    p = Path(settings.SAMPLES_DIR)
    if not p.is_absolute():
        p = _project_root() / p
    return p


def _ensure_sample_pdfs() -> list[Path]:
    """返回 samples 下的 PDF 列表；为空时尝试用 reportlab 即时生成。"""
    pdfs = sorted(_samples_dir().glob("*.pdf"))
    if pdfs:
        return pdfs
    try:
        from scripts.make_sample_pdf import main as _gen

        _gen()
        pdfs = sorted(_samples_dir().glob("*.pdf"))
        if pdfs:
            return pdfs
    except Exception as e:
        logger.warning(f"未找到示例 PDF 且无法生成（{e}），mock 附件将回退为纯文本")
    return []


# ----------------------- mock 数据 ----------------------- #

def _mock_pending(limit: int) -> list[dict[str, Any]]:
    items = []
    for i in range(1, min(limit, 5) + 1):
        code = f"AP{20260720000 + i}"
        items.append(
            {
                "approval_code": code,
                "approval_title": f"XX 采购合同审批 {i}",
                "applicant_name": f"张{i}",
                "apply_time": "2026-07-20 09:00:00",
                "attachment_count": 1,
                "instance_id": code,
            }
        )
    return items


def _mock_detail(instance_id: str) -> dict[str, Any]:
    return {
        "approval_code": instance_id,
        "approval_title": "XX 采购合同审批",
        "applicant_name": "张三",
        "apply_time": "2026-07-20 09:00:00",
        "form_data": {"contract_amount": "500000", "currency": "CNY", "department": "采购部"},
        "current_status": "审批中",
        "attachments": [
            {
                "attachment_id": f"{instance_id}-A1",
                "file_name": "采购合同.pdf",
                "file_type": "pdf",
                "file_size": 102400,
            }
        ],
    }


def _mock_attachment_bytes(instance_id: str, attachment_id: str) -> tuple[bytes, str]:
    """优先返回 samples 下真实 PDF；否则回退内置纯文本。"""
    pdfs = _ensure_sample_pdfs()
    if pdfs:
        # 用 instance_id 确定性挑选一份，保证同一审批单每次拿到同一份
        idx = zlib.crc32(instance_id.encode("utf-8")) % len(pdfs)
        target = pdfs[idx]
        content = target.read_bytes()
        logger.info(f"mock 附件取自示例 PDF: {target.name}")
        return content, hashlib.md5(content).hexdigest()

    content = (
        f"合同编号：HT-{instance_id}\n"
        f"甲方：示例科技有限公司\n"
        f"乙方：{instance_id} 供应商\n"
        f"合同金额：500000 元，币种：人民币\n"
        f"预付款比例：40%\n"
        f"付款周期：90 天\n"
        f"生效时间：2026-08-01，到期时间：2027-07-31\n"
        f"本合同包含自动续约条款，到期自动续期一年。\n"
        f"争议解决：由乙方所在地法院管辖。\n"
        "（注：samples 无 PDF 且 reportlab 未安装，使用内置文本兜底）"
    ).encode("utf-8")
    return content, hashlib.md5(content).hexdigest()


def _mock_write_comment(instance_id: str, comment: str) -> dict[str, Any]:
    return {"ok": True, "comment_id": uuid.uuid4().hex, "message": "回写成功(mock)"}


# ----------------------- 真实 HTTP 调用 ----------------------- #

def _http_get(path: str, params: dict | None = None) -> Any:
    url = f"{settings.APPROVAL_BASE_URL}{path}"
    try:
        resp = httpx.get(url, params=params, headers=_headers(), timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"审批系统 GET {url} 失败: {e}")
        raise BizException(*Errors.APPROVAL_API_FAILED, data={"reason": str(e)}) from e


def _http_post(path: str, json_body: dict | None = None) -> Any:
    url = f"{settings.APPROVAL_BASE_URL}{path}"
    try:
        resp = httpx.post(url, json=json_body or {}, headers=_headers(), timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"审批系统 POST {url} 失败: {e}")
        raise BizException(*Errors.APPROVAL_API_FAILED, data={"reason": str(e)}) from e


def _http_download(path: str) -> tuple[bytes, str]:
    url = f"{settings.APPROVAL_BASE_URL}{path}"
    try:
        resp = httpx.get(url, headers=_headers(), timeout=60.0)
        resp.raise_for_status()
        content = resp.content
        return content, hashlib.md5(content).hexdigest()
    except Exception as e:
        logger.warning(f"审批系统下载 {url} 失败: {e}")
        raise BizException(*Errors.APPROVAL_API_FAILED, data={"reason": str(e)}) from e


# ----------------------- 对外 API ----------------------- #

def list_pending(limit: int) -> list[dict[str, Any]]:
    if settings.MOCK_APPROVAL:
        return _mock_pending(limit)
    data = _http_get("/api/external/pending", {"limit": limit})
    return data.get("data", []) if isinstance(data, dict) else data


def get_approval(instance_id: str) -> dict[str, Any]:
    if settings.MOCK_APPROVAL:
        return _mock_detail(instance_id)
    return _http_get(f"/api/external/approval/{instance_id}")


def download_attachment(instance_id: str, attachment_id: str) -> tuple[bytes, str]:
    if settings.MOCK_APPROVAL:
        return _mock_attachment_bytes(instance_id, attachment_id)
    return _http_download(f"/api/external/approval/{instance_id}/attachments/{attachment_id}")


def write_comment(instance_id: str, comment: str) -> dict[str, Any]:
    if settings.MOCK_APPROVAL:
        return _mock_write_comment(instance_id, comment)
    return _http_post(f"/api/external/approval/{instance_id}/comments", {"content": comment})
