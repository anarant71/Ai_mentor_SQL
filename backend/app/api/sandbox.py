"""Sandbox API: /api/v1/sandbox/* endpoints."""

from fastapi import APIRouter, Depends

from app.middleware import require_active
from app.models.user import User
from app.schemas.sandbox import (
    SqlCheckRequest,
    SqlCheckResponse,
    SqlExecuteRequest,
    SqlExecuteResponse,
)
from app.services.sandbox import execute_sql
from app.services.validation import validate_submission

router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"])


@router.post("/execute", response_model=SqlExecuteResponse)
async def sandbox_execute(
    body: SqlExecuteRequest,
    current_user: User = Depends(require_active),
):
    """Выполнить SELECT-запрос в training_db и вернуть результат.

    Ограничения:
    - только SELECT
    - statement_timeout = 30s
    - максимум 1000 строк
    """
    from app.services.mistakes import detect_mistakes
    from app.database import PlatformSessionLocal

    try:
        result = await execute_sql(body.sql, row_limit=1000)
        return SqlExecuteResponse(**result)
    except Exception as exc:
        # Детектируем ошибки даже при неудачном выполнении
        async with PlatformSessionLocal() as session:
            await detect_mistakes(
                student_id=current_user.id,
                sql_text=body.sql,
                is_correct=False,
                session=session,
                error_text=str(exc),
            )
        raise


@router.post("/check", response_model=SqlCheckResponse)
async def sandbox_check(
    body: SqlCheckRequest,
    current_user: User = Depends(require_active),
):
    """Выполнить запрос студента и сравнить с эталоном задания.

    Предварительно загружает задание, чтобы получить expected_answer_sql.
    """
    from uuid import UUID
    from sqlalchemy import select

    from app.database import PlatformSessionLocal
    from app.models.task import Task

    # Загружаем задание (нужен доступ к expected_answer_sql)
    async with PlatformSessionLocal() as session:
        result = await session.execute(
            select(Task).where(Task.id == body.task_id)
        )
        task = result.scalar_one_or_none()

    if task is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TASK_NOT_FOUND",
                "message": "Задание не найдено",
            },
        )

    validation = await validate_submission(
        student_sql=body.sql,
        expected_sql=task.expected_answer_sql,
        strategy=task.validation_strategy,
    )

    return SqlCheckResponse(**validation)