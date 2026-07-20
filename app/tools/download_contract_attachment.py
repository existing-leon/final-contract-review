"""附件下载工具：按审批编号和附件编号下载合同附件，返回本地路径与校验信息。

下载后按内容 magic bytes 自动判定真实后缀（PDF/docx/图片/文本），
保证无论 mock（真实 PDF 或文本兜底）还是真实审批系统，都能被正确的解析器读取。
"""
import os
from typing import Any

from app.core.config import settings
from app.core.exceptions import BizException, Errors
from app.services import approval_client


def _ext_for_content(content: bytes) -> str:
    """根据文件头 magic bytes 判断扩展名。"""
    if content[:4] == b"%PDF":
        return ".pdf"
    if content[:2] == b"PK":  # docx/xlsx 等 zip 格式
        return ".docx"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if content[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if content[:2] == b"BM":
        return ".bmp"
    return ".txt"


def download_contract_attachment(
    instance_id: str, attachment_id: str, file_name: str | None = None
) -> dict[str, Any]:
    content, checksum = approval_client.download_attachment(instance_id, str(attachment_id))
    if not content:
        raise BizException(*Errors.ATTACHMENT_MISSING, data={"attachment_id": attachment_id})

    os.makedirs(settings.ATTACHMENT_DIR, exist_ok=True)
    # 按内容 magic 判定后缀：mock 的真实 PDF → .pdf；文本兜底 → .txt
    base = os.path.splitext(file_name)[0] if file_name else f"{instance_id}_{attachment_id}"
    safe_name = f"{base}{_ext_for_content(content)}"
    file_path = os.path.join(settings.ATTACHMENT_DIR, safe_name)

    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "file_path": file_path,
        "checksum": checksum,
        "file_size": len(content),
        "file_name": safe_name,
    }
