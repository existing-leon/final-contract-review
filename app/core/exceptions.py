"""自定义业务异常与全局异常处理器。"""
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core import response


class BizException(Exception):
    """业务异常，携带 code/message/data。"""

    def __init__(self, code: int = 9000, message: str = "系统内部错误", data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class InvalidStateTransition(BizException):
    def __init__(self, message: str = "非法状态迁移"):
        super().__init__(1003, message)


class Errors:
    """业务错误码表（与后端手册 4.2 对齐）。"""

    PARAM_ERROR = (1000, "参数错误")
    UNAUTHORIZED = (1001, "未授权")
    NOT_FOUND = (1002, "资源不存在")
    INVALID_STATE = (1003, "非法状态迁移")
    ATTACHMENT_MISSING = (2001, "附件缺失")
    DOC_EMPTY = (2002, "文档内容为空")
    OCR_FAILED = (2003, "OCR 识别失败")
    APPROVAL_API_FAILED = (2004, "审批系统接口调用失败")
    WRITE_FAILED = (2005, "回写失败")
    SYSTEM_ERROR = (9000, "系统内部错误")

    @classmethod
    def raise_(cls, pair: tuple[int, str], data: Any = None) -> None:
        code, message = pair
        raise BizException(code, message, data)


async def biz_exception_handler(_: Request, exc: BizException) -> JSONResponse:
    return JSONResponse(response.error(exc.code, exc.message, exc.data))


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    from app.core.logger import logger

    logger.exception(f"未处理异常: {exc}")
    return JSONResponse(response.error(9000, "系统内部错误"))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BizException, biz_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
