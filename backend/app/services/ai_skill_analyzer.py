"""AI Skill Analyzer — анализ навыков студента через Nvidia Nemotron API."""

import json
import logging
from decimal import Decimal
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """Ты — AI-наставник SQL на мебельной фабрике. Твой студент учится SQL.
После каждой проверки задания ты оцениваешь его навыки и даёшь обратную связь.

Правила анализа:
1. Оценивай КАЖДЫЙ навык из списка task_skills по шкале 0.0-1.0
2. Если студент ответил верно (is_correct=true) — score >= 0.7
3. Если неверно — score < 0.5, укажи что именно пошло не так
4. Комментарии пиши на русском, обращайся на "ты"
5. Определи 1-2 слабые зоны (weak_areas)
6. next_focus — навык, который стоит тренировать следующим

Ответь строгим JSON без markdown-разметки:
{
  "skill_scores": [
    {"code": "where_filter", "score": 0.8, "comment": "Ты верно использовал WHERE с кавычками"},
    {"code": "select_basic", "score": 0.9, "comment": "Колонки выбраны правильно"}
  ],
  "feedback": "Отличная работа! ...",
  "weak_areas": ["where_filter"],
  "next_focus": "join"
}"""


async def analyze_skills(
    student_sql: str,
    expected_sql: str,
    task_skills: list[dict],
    is_correct: bool,
    attempt_number: int,
    student_name: str = "Student",
    lesson_title: str = "",
    task_title: str = "",
) -> dict:
    """Анализирует навыки студента через Nvidia Nemotron API.

    Args:
        student_sql: SQL-запрос студента.
        expected_sql: эталонный SQL.
        task_skills: список навыков задания [{"code": str, "weight": float, "title": str}].
        is_correct: результат валидации.
        attempt_number: номер попытки.
        student_name: имя студента.
        lesson_title: название урока.
        task_title: название задания.

    Returns:
        {"skill_scores": [...], "feedback": str, "weak_areas": [...], "next_focus": str|None}
    """
    if not settings.NVIDIA_API_KEY:
        return _fallback_analysis(task_skills, is_correct)

    skills_text = "\n".join(
        f"- {s['code']} ({s.get('title', '')}, weight={s.get('weight', 1.0)})"
        for s in task_skills
    )

    user_prompt = f"""Студент: {student_name}
Урок: {lesson_title}
Задание: {task_title}
Попытка №: {attempt_number}

SQL студента:
```sql
{student_sql}
```

Эталонный SQL:
```sql
{expected_sql}
```

Результат проверки: {'верно' if is_correct else 'неверно'}

Навыки в задании:
{skills_text}"""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{settings.NVIDIA_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.NVIDIA_MODEL,
                    "messages": [
                        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 800,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # Clean potential markdown fences
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
            content = content.strip()

            result = json.loads(content)
            _validate_result(result, task_skills)
            return result

    except Exception as exc:
        logger.warning(f"AI skill analysis failed: {exc}")
        return _fallback_analysis(task_skills, is_correct)


def _validate_result(result: dict, task_skills: list[dict]) -> None:
    """Проверяет, что ответ AI содержит все нужные поля."""
    assert "skill_scores" in result, "Missing skill_scores"
    assert "feedback" in result, "Missing feedback"
    assert "weak_areas" in result, "Missing weak_areas"

    expected_codes = {s["code"] for s in task_skills}
    result_codes = {s["code"] for s in result["skill_scores"]}
    missing = expected_codes - result_codes
    if missing:
        for code in missing:
            result["skill_scores"].append({
                "code": code,
                "score": 0.5,
                "comment": "Не удалось оценить навык",
            })


def _fallback_analysis(
    task_skills: list[dict],
    is_correct: bool,
) -> dict:
    """Fallback-анализ без вызова AI."""
    base_score = 0.85 if is_correct else 0.35
    skill_scores = []
    weak_areas = []

    for s in task_skills:
        score = base_score * s.get("weight", 1.0)
        skill_scores.append({
            "code": s["code"],
            "score": round(min(score, 1.0), 2),
            "comment": "Верно!" if is_correct else "Есть ошибки",
        })
        if not is_correct:
            weak_areas.append(s["code"])

    return {
        "skill_scores": skill_scores,
        "feedback": "Задание выполнено верно!" if is_correct else "Есть ошибки в решении. Попробуй ещё раз.",
        "weak_areas": weak_areas,
        "next_focus": weak_areas[0] if weak_areas else None,
    }