"""统一响应封装。所有接口返回 {code, message, data, trace_id}。"""
import uuid
from typing import Any


def success(data: Any = None, message: str = "success") -> dict:
    return {
        "code": 0,
        "message": message,
        "data": data,
        "trace_id": uuid.uuid4().hex,
    }


def error(code: int, message: str, data: Any = None) -> dict:
    return {
        "code": code,
        "message": message,
        "data": data,
        "trace_id": uuid.uuid4().hex,
    }


class ApiResponse:
    success = staticmethod(success)
    error = staticmethod(error)
