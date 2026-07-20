"""文档解析工具：对已下载合同执行解析，输出结构化字段、原文片段和定位信息。"""
from typing import Any

from app.core.constants import ParseStatus
from app.core.database import SessionLocal
from app.core.exceptions import BizException, Errors
from app.engine.llm_extractor import extract_smart
from app.engine.parser import parse_file
from app.models import ApprovalAttachment


def parse_contract_document(document_id: int, db=None) -> dict[str, Any]:
    """document_id 对应 approval_attachments.id，按其 file_path 解析。

    字段提取优先用 LLM（配置了 LLM_API_KEY 时），失败或未配置则自动回退正则。
    """
    own = db is None
    db = db or SessionLocal()
    try:
        attachment = db.get(ApprovalAttachment, document_id)
        if not attachment or not attachment.file_path:
            raise BizException(*Errors.NOT_FOUND, data={"document_id": document_id})

        parsed = parse_file(attachment.file_path)  # 失败抛 DOC_EMPTY / OCR_FAILED
        basic_info, clause_info, snippets, meta = extract_smart(parsed)
        # 注入合同原文，供规则引擎做全文匹配（keyword/regex/threshold）
        full_text = parsed.get("text", "")
        for table_text in (parsed.get("tables") or []):
            full_text += "\n" + table_text
        basic_info["_full_text"] = full_text

        return {
            "task_id": attachment.task_id,
            "document_id": document_id,
            "parse_status": ParseStatus.SUCCESS,
            "basic_info": basic_info,
            "clause_info": clause_info,
            "snippets": snippets,
            "parse_error": None,
            "extract_method": meta.get("method"),
            "llm_model": meta.get("model"),
        }
    finally:
        if own:
            db.close()
