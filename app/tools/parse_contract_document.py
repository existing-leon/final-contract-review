"""文档解析工具：对已下载合同执行解析，输出结构化字段、原文片段和定位信息。"""
from typing import Any

from app.core.constants import ParseStatus
from app.core.database import SessionLocal
from app.core.exceptions import BizException, Errors
from app.engine.field_extractor import extract_fields
from app.engine.parser import parse_file
from app.models import ApprovalAttachment


def parse_contract_document(document_id: int, db=None) -> dict[str, Any]:
    """document_id 对应 approval_attachments.id，按其 file_path 解析。"""
    own = db is None
    db = db or SessionLocal()
    try:
        attachment = db.get(ApprovalAttachment, document_id)
        if not attachment or not attachment.file_path:
            raise BizException(*Errors.NOT_FOUND, data={"document_id": document_id})

        parsed = parse_file(attachment.file_path)  # 失败抛 DOC_EMPTY / OCR_FAILED
        basic_info, clause_info, snippets = extract_fields(parsed)
        # 注入合同原文，供规则引擎做全文匹配（keyword/regex/threshold）
        basic_info["_full_text"] = parsed.get("text", "")

        return {
            "task_id": attachment.task_id,
            "document_id": document_id,
            "parse_status": ParseStatus.SUCCESS,
            "basic_info": basic_info,
            "clause_info": clause_info,
            "snippets": snippets,
            "parse_error": None,
        }
    finally:
        if own:
            db.close()
