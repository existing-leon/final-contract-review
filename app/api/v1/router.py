"""v1 路由聚合。"""
from fastapi import APIRouter

from app.api.v1 import approvals, attachments, logs, parses, results, rules, tasks

api_router = APIRouter()

api_router.include_router(approvals.router, prefix="/approvals", tags=["待办与审批"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务"])
api_router.include_router(attachments.router, tags=["附件"])
api_router.include_router(parses.router, tags=["解析"])
api_router.include_router(results.router, tags=["规则审查/结果/回写"])
api_router.include_router(logs.router, tags=["日志"])
api_router.include_router(rules.router, prefix="/rules", tags=["规则管理"])
