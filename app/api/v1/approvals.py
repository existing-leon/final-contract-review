from fastapi import APIRouter, Depends, Query

from app.core import response
from app.core.security import get_current_user
from app.models import User
from app.tools import get_contract_approval, list_pending_contract_approvals

router = APIRouter()


@router.get("/pending")
def pending(
    limit: int = Query(20, ge=1, le=100),
    _user: User = Depends(get_current_user),
):
    """查询待处理审批单列表。"""
    return response.success(list_pending_contract_approvals(limit))


@router.get("/{instance_id}")
def detail(instance_id: str, _user: User = Depends(get_current_user)):
    """查询单个审批单详情。"""
    return response.success(get_contract_approval(instance_id))
