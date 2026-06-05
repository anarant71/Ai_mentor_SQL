"""Sandbox service: безопасное выполнение SQL в training_db.

Проверки безопасности:
- только SELECT/WITH запросы (через sqlparse)
- statement_timeout = 30s
- максимум 1000 строк (только sandbox/execute)
"""

import time

import sqlparse
from fastapi import HTTPException, status
from sqlalchemy import text

from app.database import training_engine
from app.config import settings

# Токены, запрещённые в любом положении
_FORBIDDEN_KEYWORDS = frozenset({
    "INSERT", "UPDATE", "DELETE", "DROP",
    "ALTER", "CREATE", "TRUNCATE", "COPY",
    "EXECUTE", "IMPORT", "GRANT", "REVOKE",
    "REPLACE", "MERGE", "LOAD", "UNLOAD",
})


def validate_select_only(sql: str) -> str:
    """Проверить, что запрос безопасен для выполнения.

    1. Парсит SQL через sqlparse
    2. Проверяет, что все statements — SELECT или CTE
    3. Блокирует модифицирующие запросы в любом положении (включая CTE)
    """
    stripped = sql.strip().rstrip(";").strip()

    if not stripped:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMPTY_QUERY",
                "message": "Запрос не может быть пустым",
            },
        )

    try:
        parsed = sqlparse.parse(stripped)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SQL_PARSE_ERROR",
                "message": "Не удалось разобрать SQL-запрос",
            },
        )

    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMPTY_QUERY",
                "message": "Запрос не содержит SQL-выражений",
            },
        )

    allowed_cte_setups = frozenset({"SELECT", "WITH", "TABLE", "VALUES"})

    for statement in parsed:
        stmt_type = statement.get_type().upper()

        # Проверка верхнеуровневого типа
        if stmt_type not in allowed_cte_setups:
            if stmt_type in _FORBIDDEN_KEYWORDS:
                msg = (
                    f"Запрещённый тип запроса: {stmt_type}. "
                    f"Разрешены только SELECT и WITH (CTE) запросы."
                )
            else:
                msg = (
                    f"Разрешены только SELECT и WITH (CTE) запросы, "
                    f"получен: {stmt_type}."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "NOT_SELECT_QUERY",
                    "message": msg,
                },
            )

        # Рекурсивная проверка всех токенов на наличие forbidden keywords
        _check_forbidden_in_children(statement)

    return stripped


def _check_forbidden_in_children(token) -> None:
    """Рекурсивно проверяет все дочерние токены на forbidden keywords.

    Позволяет обнаружить DDL/DML внутри CTE (WITH ... AS (INSERT INTO ...)).
    """
    if token.ttype in (sqlparse.tokens.Keyword.DDL, sqlparse.tokens.Keyword.DML):
        kw = token.value.upper()
        if kw in _FORBIDDEN_KEYWORDS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "FORBIDDEN_STATEMENT_IN_CTE",
                    "message": (
                        f"Обнаружен запрещённый оператор '{kw}' внутри запроса. "
                        f"Разрешены только SELECT и WITH."
                    ),
                },
            )

    if hasattr(token, "tokens"):
        for sub_token in token.tokens:
            _check_forbidden_in_children(sub_token)


def _serialize_value(val):
    """Преобразовать значение в JSON-сериализуемый тип."""
    if val is None:
        return None
    if isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(val, (dict, list)):
        return val
    # UUID, datetime, Decimal и т.д. → строка
    return str(val)


async def execute_sql(sql: str, row_limit: int = 1000) -> dict:
    """Выполнить SELECT в training_db и вернуть результат.

    Args:
        sql: SQL-запрос (только SELECT).
        row_limit: максимум строк (по умолчанию 1000).

    Returns:
        {"columns": [...], "rows": [[...], ...], "row_count": N, "execution_time_ms": N}
    """
    clean_sql = validate_select_only(sql)
    timeout_ms = settings.TRAINING_STATEMENT_TIMEOUT * 1000

    start = time.monotonic()

    try:
        async with training_engine.connect() as conn:
            # Устанавливаем таймаут
            await conn.execute(text(f"SET statement_timeout = '{timeout_ms}'"))

            # Выполняем запрос
            result = await conn.execute(text(clean_sql))
            columns = list(result.keys())
            raw_rows = result.fetchmany(row_limit)
            rows = [[_serialize_value(v) for v in row] for row in raw_rows]

    except Exception as exc:
        error_msg = str(exc)
        # Пытаемся вытащить человекочитаемую часть ошибки PostgreSQL
        # Типичный формат: "(psycopg2.errors.X) DETAIL: ...\n..."
        if "DETAIL:" in error_msg:
            detail_part = error_msg.split("DETAIL:")[-1].strip().split("\n")[0].strip()
            error_msg = detail_part
        elif ":" in error_msg:
            # Берём последнюю часть после двоеточия
            parts = error_msg.split(":")
            error_msg = parts[-1].strip()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SQL_EXECUTION_ERROR",
                "message": f"Ошибка при выполнении запроса: {error_msg}",
            },
        )

    elapsed_ms = int((time.monotonic() - start) * 1000)

    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "execution_time_ms": elapsed_ms,
    }


async def execute_sql_for_validation(sql: str) -> dict:
    """Выполнить SQL для проверки (без принудительного LIMIT).

    Используется в validation.py для сравнения student ↔ expected.
    """
    clean_sql = validate_select_only(sql)
    timeout_ms = settings.TRAINING_STATEMENT_TIMEOUT * 1000

    try:
        async with training_engine.connect() as conn:
            await conn.execute(text(f"SET statement_timeout = '{timeout_ms}'"))
            result = await conn.execute(text(clean_sql))
            columns = list(result.keys())
            raw_rows = result.fetchall()
            rows = [[_serialize_value(v) for v in row] for row in raw_rows]
    except Exception as exc:
        error_msg = str(exc)
        if "DETAIL:" in error_msg:
            detail_part = error_msg.split("DETAIL:")[-1].strip().split("\n")[0].strip()
            error_msg = detail_part
        elif ":" in error_msg:
            parts = error_msg.split(":")
            error_msg = parts[-1].strip()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SQL_EXECUTION_ERROR",
                "message": f"Ошибка при выполнении запроса: {error_msg}",
            },
        )

    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
    }