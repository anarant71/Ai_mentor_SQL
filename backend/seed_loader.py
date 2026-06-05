"""Seed loader for AI-Mentor platform.

Загружает уроки, задания и привязку навыков в БД.
Idempotent + upsert: обновляет существующие записи если они изменились.

Usage:
    cd backend/
    python -m seed_loader
"""

import asyncio
import uuid

from app.database import PlatformSessionLocal
from app.models.lesson import Lesson
from app.models.task import Task
from app.models.skill import Skill, TaskSkill

# ---------------------------------------------------------------------------
# Seed data: Module 0 — "Введение в SQL и базы данных"
# ---------------------------------------------------------------------------

SEED_LESSONS = [
    {
        "module_number": 0,
        "lesson_number": 1,
        "slug": "lesson-01",
        "title": "Первый SQL-запрос",
        "module_title": "Введение в SQL и базы данных",
        "summary": "Первый SQL-запрос. Знакомство с SELECT *, таблицами chair_models и materials.",
        "content_path": "lesson_01.md",
        "difficulty": 1,
        "estimated_minutes": 15,
        "status": "published",
        "tasks": [
            {
                "slug": "task-01-01",
                "title": "Первый SELECT",
                "description": "SELECT — первая команда SQL. Просто загляни в таблицу materials и посмотри, какие данные там хранятся.",
                "instructions": "### Условие\n\nВыполни запрос к таблице materials.\n\nИспользуй SELECT * FROM materials;\n\nПосмотри на результат и ответь:\n1. Сколько строк в таблице?\n2. Какие категории материалов есть?\n3. Какие единицы измерения используются?\n\n### Критерии проверки\n\n- Запрос выполнился без ошибок\n- Использована таблица materials\n- Результат содержит строки (таблица не пустая)",
                "expected_result_text": "Таблица со всеми колонками из materials. Не менее 20 строк.",
                "hint": "SELECT * FROM materials;",
                "expected_answer_sql": "SELECT * FROM materials;",
                "validation_strategy": "not_empty",
                "difficulty": 1,
                "status": "published",
                "skill_codes": ["select_basic"],
            }
        ],
    },
    {
        "module_number": 0,
        "lesson_number": 2,
        "slug": "lesson-02",
        "title": "Выбор колонок и синтаксис SQL",
        "module_title": "Введение в SQL и базы данных",
        "summary": "Явный перечень колонок, порядок SELECT -> FROM, разница между SELECT * и конкретными колонками.",
        "content_path": "lesson_02.md",
        "difficulty": 1,
        "estimated_minutes": 20,
        "status": "published",
        "tasks": [
            {
                "slug": "task-02-01",
                "title": "Выбор колонок",
                "description": "Научись выбирать только нужные колонки вместо SELECT *.",
                "instructions": "### Условие\n\nНапиши запрос, который показывает material_code, material_name и current_price из таблицы materials.\n\nКолонки должны идти именно в таком порядке: код, название, цена.\n\n### Ожидаемый результат\n\nТри колонки: material_code, material_name, current_price. Каждая строка — один материал.\n\n### Критерии проверки\n\n- В SELECT перечислены три колонки: material_code, material_name, current_price\n- Колонки идут в указанном порядке\n- FROM materials\n- Запрос не использует WHERE, JOIN, GROUP BY",
                "expected_result_text": "Три колонки: material_code, material_name, current_price.",
                "hint": "SELECT material_code, material_name, current_price FROM materials;",
                "expected_answer_sql": "SELECT\n    material_code,\n    material_name,\n    current_price\nFROM materials;",
                "validation_strategy": "exact_match",
                "difficulty": 1,
                "status": "published",
                "skill_codes": ["select_basic"],
            }
        ],
    },
    {
        "module_number": 0,
        "lesson_number": 3,
        "slug": "lesson-03",
        "title": "Фильтрация строк через WHERE",
        "module_title": "Введение в SQL и базы данных",
        "summary": "Фильтрация строк через WHERE, синтаксис SELECT -> FROM -> WHERE, кавычки для текстовых значений.",
        "content_path": "lesson_03.md",
        "difficulty": 2,
        "estimated_minutes": 25,
        "status": "published",
        "tasks": [
            {
                "slug": "task-03-01",
                "title": "Фильтрация WHERE",
                "description": "WHERE нужен, чтобы не смотреть всю таблицу, а сразу находить нужные строки.",
                "instructions": "### Условие\n\nНайди все активные модели кресел из таблицы chair_models.\n\nПокажи колонки:\n- model_code\n- model_name\n- category\n- status\n- standard_labor_minutes\n\n### Ожидаемый результат\n\nТолько модели со статусом active. Тестовые и архивные не должны попасть в результат.\n\n### Критерии проверки\n\n- Использована только таблица chair_models\n- В запросе есть SELECT, FROM и WHERE\n- Условие проверяет status = 'active'\n- Выбраны только колонки из условия",
                "expected_result_text": "Список активных моделей кресел: model_code, model_name, category, status, standard_labor_minutes.",
                "hint": "SELECT model_code, model_name, category, status, standard_labor_minutes FROM chair_models WHERE status = 'active';",
                "expected_answer_sql": "SELECT\n    model_code,\n    model_name,\n    category,\n    status,\n    standard_labor_minutes\nFROM chair_models\nWHERE status = 'active';",
                "validation_strategy": "exact_match",
                "difficulty": 2,
                "status": "published",
                "skill_codes": ["where_filter", "select_basic"],
            }
        ],
    },
    {
        "module_number": 0,
        "lesson_number": 4,
        "slug": "lesson-04",
        "title": "SELECT и FROM. Выбор колонок",
        "module_title": "Введение в SQL и базы данных",
        "summary": "Осознанный выбор колонок из таблиц chair_models и materials для конкретных производственных задач.",
        "content_path": "lesson_04.md",
        "difficulty": 2,
        "estimated_minutes": 25,
        "status": "published",
        "tasks": [
            {
                "slug": "task-04-01",
                "title": "Справочник материалов",
                "description": "Выведи полный справочник материалов из таблицы materials с нужными экономисту колонками.",
                "instructions": "### Условие\n\nВыведи справочник материалов из таблицы materials.\n\nПокажи только эти колонки в указанном порядке:\n1. material_code — код материала\n2. material_name — название материала\n3. category — категория материала\n4. unit — единица измерения\n5. current_price — текущая цена\n6. status — статус материала\n\n### Ожидаемый результат\n\n6 колонок. Каждая строка — один материал.\n\nЭкономисту такой запрос нужен чтобы быстро проверить:\n- какие материалы есть в базе\n- какие категории представлены\n- какие цены установлены\n- какие материалы активны\n\n### Критерии проверки\n\n- Использована только таблица materials\n- В SELECT перечислены ровно 6 колонок из условия\n- Колонки идут в указанном порядке\n- Запрос не использует WHERE, JOIN, GROUP BY",
                "expected_result_text": "6 колонок: material_code, material_name, category, unit, current_price, status.",
                "hint": "SELECT\n    material_code,\n    material_name,\n    category,\n    unit,\n    current_price,\n    status\nFROM materials;",
                "expected_answer_sql": "SELECT\n    material_code,\n    material_name,\n    category,\n    unit,\n    current_price,\n    status\nFROM materials;",
                "validation_strategy": "exact_match",
                "difficulty": 2,
                "status": "published",
                "skill_codes": ["select_basic"],
            }
        ],
    },
    {
        "module_number": 0,
        "lesson_number": 5,
        "slug": "lesson-05",
        "title": "WHERE и AND",
        "module_title": "Введение в SQL и базы данных",
        "summary": "Фильтрация строк через WHERE, логические операторы AND/OR и применение фильтров в производственных отчётах.",
        "content_path": "lesson_05.md",
        "difficulty": 2,
        "estimated_minutes": 25,
        "status": "published",
        "tasks": [
            {
                "slug": "task-05-01",
                "title": "Фильтрация с AND",
                "description": "Научись соединять несколько условий через AND: найди активные материалы конкретной категории.",
                "instructions": "### Условие\n\nНайди все активные материалы категории fabric (ткань) из таблицы materials.\n\nПокажи колонки:\n- material_code\n- material_name\n- category\n- current_price\n- status\n\n### Ожидаемый результат\n\nТолько материалы, где одновременно category = 'fabric' и status = 'active'.\n\nДля экономиста это важно: видеть только актуальные ткани для расчёта себестоимости.\n\n### Критерии проверки\n\n- Использована только таблица materials\n- В запросе есть SELECT, FROM и WHERE\n- В WHERE два условия, соединённые через AND\n- Первое условие: category = 'fabric'\n- Второе условие: status = 'active'\n- Выбраны только колонки из условия",
                "expected_result_text": "Активные материалы категории fabric: material_code, material_name, category, current_price, status.",
                "hint": "SELECT\n    material_code,\n    material_name,\n    category,\n    current_price,\n    status\nFROM materials\nWHERE category = 'fabric'\n  AND status = 'active';",
                "expected_answer_sql": "SELECT\n    material_code,\n    material_name,\n    category,\n    current_price,\n    status\nFROM materials\nWHERE category = 'fabric'\n  AND status = 'active';",
                "validation_strategy": "exact_match",
                "difficulty": 2,
                "status": "published",
                "skill_codes": ["where_filter", "select_basic"],
            }
        ],
    },
]

# ---------------------------------------------------------------------------
# Standalone tasks for TaskBook (not tied to a specific lesson)
# ---------------------------------------------------------------------------

STANDALONE_TASKS = [
    {
        "slug": "practice-order-limit-01",
        "title": "Топ-3 по трудоёмкости",
        "description": "Найди три самые трудоёмкие модели кресел.",
        "instructions": "### Условие\n\nВыведи три самые трудоёмкие модели кресел из таблицы chair_models.\n\nПокажи колонки:\n- model_code\n- model_name\n- category\n- standard_labor_minutes\n\nОтсортируй по убыванию standard_labor_minutes и оставь только 3 строки.\n\n### Критерии проверки\n\n- Использована таблица chair_models\n- Есть ORDER BY standard_labor_minutes DESC\n- Есть LIMIT 3",
        "expected_result_text": "Три самые трудоёмкие модели кресел, от самой трудоёмкой к менее трудоёмкой.",
        "hint": "SELECT ... FROM chair_models ORDER BY standard_labor_minutes DESC LIMIT 3;",
        "expected_answer_sql": "SELECT\n    model_code,\n    model_name,\n    category,\n    standard_labor_minutes\nFROM chair_models\nORDER BY standard_labor_minutes DESC\nLIMIT 3;",
        "validation_strategy": "exact_match",
        "difficulty": 2,
        "status": "published",
        "skill_codes": ["order_limit", "select_basic"],
    },
    {
        "slug": "practice-group-by-01",
        "title": "Плановый выпуск по моделям",
        "description": "Посчитай общий плановый выпуск по каждой модели кресел.",
        "instructions": "### Условие\n\nПосчитай плановое количество кресел по каждой модели из таблицы production_plan.\n\nПокажи:\n- chair_model_id\n- сумму planned_quantity с алиасом total_planned_quantity\n\nИспользуй только строки, у которых status = 'approved'.\n\n### Критерии проверки\n\n- Использована только таблица production_plan\n- Есть фильтр WHERE status = 'approved'\n- Использована агрегатная функция SUM\n- Есть GROUP BY chair_model_id\n- Сумма имеет алиас total_planned_quantity",
        "expected_result_text": "По каждой модели из production_plan — общее плановое количество (SUM planned_quantity) со статусом approved.",
        "hint": "SELECT chair_model_id, SUM(planned_quantity) AS total_planned_quantity FROM production_plan WHERE status = 'approved' GROUP BY chair_model_id;",
        "expected_answer_sql": "SELECT\n    chair_model_id,\n    SUM(planned_quantity) AS total_planned_quantity\nFROM production_plan\nWHERE status = 'approved'\nGROUP BY chair_model_id;",
        "validation_strategy": "exact_match",
        "difficulty": 3,
        "status": "published",
        "skill_codes": ["group_by", "where_filter"],
    },
    {
        "slug": "practice-join-01",
        "title": "План с названиями моделей",
        "description": "Соедини план производства со справочником моделей, чтобы получить понятный отчёт.",
        "instructions": "### Условие\n\nВыведи план производства вместе с кодом и названием модели кресла.\n\nИспользуй таблицы:\n- production_plan\n- chair_models\n\nПокажи колонки:\n- plan_date\n- model_code\n- model_name\n- planned_quantity\n- status\n\n### Критерии проверки\n\n- Использованы только production_plan и chair_models\n- Есть JOIN\n- В ON правильно связаны cm.id и pp.chair_model_id",
        "expected_result_text": "План производства с понятными названиями моделей кресел. Колонки: plan_date, model_code, model_name, planned_quantity, status.",
        "hint": "SELECT ... FROM production_plan AS pp JOIN chair_models AS cm ON cm.id = pp.chair_model_id;",
        "expected_answer_sql": "SELECT\n    pp.plan_date,\n    cm.model_code,\n    cm.model_name,\n    pp.planned_quantity,\n    pp.status\nFROM production_plan AS pp\nJOIN chair_models AS cm\n    ON cm.id = pp.chair_model_id;",
        "validation_strategy": "exact_match",
        "difficulty": 3,
        "status": "published",
        "skill_codes": ["join", "select_basic"],
    },
]


async def _get_skill_map(session) -> dict[str, Skill]:
    """Загружает все навыки из БД в словарь code -> Skill."""
    from sqlalchemy import select
    result = await session.execute(select(Skill))
    return {s.code: s for s in result.scalars().all()}


async def _upsert_task(
    session,
    lesson_id: uuid.UUID | None,
    task_data: dict,
    skill_map: dict[str, Skill],
) -> Task:
    """Создаёт или обновляет задание и привязывает навыки."""
    from sqlalchemy import select

    skill_codes = task_data.pop("skill_codes", [])
    slug = task_data["slug"]

    result = await session.execute(select(Task).where(Task.slug == slug))
    task = result.scalar_one_or_none()

    if task is None:
        task = Task(lesson_id=lesson_id, **task_data)
        session.add(task)
        await session.flush()
        print(f"    + Task: {slug} — {task_data['title']}")
    else:
        changed = False
        for key, value in task_data.items():
            if getattr(task, key) != value:
                setattr(task, key, value)
                changed = True
        if lesson_id is not None:
            task.lesson_id = lesson_id
        if changed:
            print(f"    ~ Task: {slug} — updated")
        else:
            print(f"    = Task: {slug} — unchanged")

    # Update skill tags: remove old, add new
    if skill_codes and skill_map:
        existing_skills = await session.execute(
            select(TaskSkill).where(TaskSkill.task_id == task.id)
        )
        existing_ids = {ts.skill_id for ts in existing_skills.scalars().all()}
        desired_ids = set()
        for code in skill_codes:
            skill = skill_map.get(code)
            if skill is not None:
                desired_ids.add(skill.id)

        # Remove old tags not in desired set
        for ts in existing_skills.scalars().all():
            if ts.skill_id not in desired_ids:
                await session.delete(ts)

        # Add new tags not in existing set
        for sid in desired_ids:
            if sid not in existing_ids:
                ts = TaskSkill(task_id=task.id, skill_id=sid)
                session.add(ts)

    return task


async def seed() -> dict[str, int]:
    """Загружает seed-данные в БД. Idempotent + upsert."""
    from sqlalchemy import select

    lessons_created = 0
    tasks_created = 0
    standalone_created = 0

    async with PlatformSessionLocal() as session:
        skill_map = await _get_skill_map(session)

        for lesson_data in SEED_LESSONS:
            tasks_data = lesson_data.pop("tasks")

            result = await session.execute(
                select(Lesson).where(Lesson.slug == lesson_data["slug"])
            )
            lesson = result.scalar_one_or_none()

            if lesson is None:
                lesson = Lesson(**lesson_data)
                session.add(lesson)
                await session.flush()
                lessons_created += 1
                print(f"  + Lesson: {lesson_data['slug']} — {lesson_data['title']}")
            else:
                changed = False
                for key, value in lesson_data.items():
                    if getattr(lesson, key) != value:
                        setattr(lesson, key, value)
                        changed = True
                if changed:
                    print(f"  ~ Lesson: {lesson_data['slug']} — updated")
                else:
                    print(f"  = Lesson: {lesson_data['slug']} — unchanged")

            for task_data in tasks_data:
                await _upsert_task(session, lesson.id, task_data, skill_map)
                tasks_created += 1

        # Standalone tasks (no lesson_id)
        for task_data in STANDALONE_TASKS:
            await _upsert_task(session, None, task_data, skill_map)
            standalone_created += 1

        await session.commit()

    return {
        "lessons_created": lessons_created,
        "tasks_created": tasks_created,
        "standalone_created": standalone_created,
    }


def main():
    """Entry point."""
    print("=== AI-Mentor Seed Loader ===")
    print("Loading Module 0: Введение в SQL и базы данных\n")

    counts = asyncio.run(seed())

    print(
        f"\nDone: {counts['lessons_created']} lessons, "
        f"{counts['tasks_created']} tasks, "
        f"{counts['standalone_created']} standalone tasks created."
    )


if __name__ == "__main__":
    main()