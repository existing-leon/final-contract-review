"""待办拉取工具：返回待处理审批单列表。"""
from typing import Any

from app.services import approval_client


def list_pending_contract_approvals(limit: int = 20) -> list[dict[str, Any]]:
    """拉取待处理审批单列表，字段至少包含审批编号、标题、申请人、申请时间、附件数量。"""
    items = approval_client.list_pending(limit)
    normalized: list[dict[str, Any]] = []
    for it in items:
        normalized.append(
            {
                "approval_code": it.get("approval_code") or it.get("instance_id"),
                "approval_title": it.get("approval_title", ""),
                "applicant_name": it.get("applicant_name", ""),
                "apply_time": it.get("apply_time"),
                "attachment_count": it.get("attachment_count", 0),
                "instance_id": it.get("instance_id") or it.get("approval_code"),
            }
        )
    return normalized
