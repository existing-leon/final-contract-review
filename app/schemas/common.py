from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None
    trace_id: str = ""


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PageResult(BaseModel, Generic[T]):
    total: int = 0
    items: list[T] = []
