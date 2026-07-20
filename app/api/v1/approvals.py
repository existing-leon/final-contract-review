from fastapi import APIRouter, Query

from app.core import response
from app.tools import get_contract_approval, list_pending_contract_approvals

router = APIRouter()


@router.get("/pending")
def pending(limit: int = Query(20, ge=1, le=100)):
    """查询待处理审批单列表。"""
    return response.success(list_pending_contract_approvals(limit))


@router.get("/{instance_id}")
def detail(instance_id: str):
    """查询单个审批单详情。"""
    return response.success(get_contract_approval(instance_id))
