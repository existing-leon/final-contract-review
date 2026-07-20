"""审批详情工具：返回单个审批单详情。"""
from typing import Any

from app.services import approval_client


def get_contract_approval(instance_id: str) -> dict[str, Any]:
    """返回审批信息、表单数据、附件信息和当前处理状态。"""
    detail = approval_client.get_approval(instance_id)
    return {
        "approval_code": detail.get("approval_code") or instance_id,
        "approval_title": detail.get("approval_title", ""),
        "applicant_name": detail.get("applicant_name", ""),
        "apply_time": detail.get("apply_time"),
        "form_data": detail.get("form_data", {}),
        "current_status": detail.get("current_status", ""),
        "attachments": detail.get("attachments", []),
    }
