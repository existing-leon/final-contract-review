from typing import Any, Optional

from pydantic import BaseModel


class ParsedField(BaseModel):
    value: Optional[str] = None
    snippet: Optional[str] = None
    page: Optional[str] = None
    extract_status: str = "success"


class ParseRequest(BaseModel):
    document_id: int


class ParseResult(BaseModel):
    task_id: int
    parse_status: str
    basic_info: dict[str, Any] = {}
    clause_info: dict[str, Any] = {}
    snippets: list[dict[str, Any]] = []
    parse_error: Optional[str] = None
