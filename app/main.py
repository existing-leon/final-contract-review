"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 启动钩子（可在此预热连接池等）
    yield
    # 关闭钩子


def create_app() -> FastAPI:
    app = FastAPI(
        title="合同审批审查系统",
        description="企业合同审批场景的自动审查系统（辅助审批，不替代人工）",
        version="1.0.0",
        lifespan=lifespan,
    )
    # 跨域资源共享
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
