"""Sandbox schemas: выполнение SQL и проверка."""

from uuid import UUID

from pydantic import BaseModel


class SqlExecuteRequest(BaseModel):
    sql: str


class SqlExecuteResponse(BaseModel):
    columns: list[str]
    rows: list[list]
    row_count: int
    execution_time_ms: int


class SqlCheckRequest(BaseModel):
    task_id: UUID
    sql: str


class SqlCheckResponse(BaseModel):
    is_correct: bool
    match_type: str  # "exact" | "different"
    differences: list[str]