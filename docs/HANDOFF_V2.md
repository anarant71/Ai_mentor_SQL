# Handoff V2 — Skills, AI Mentor, TaskBook, Lesson fixes

> **Дата:** 2026-05-29
> **Статус:** MVP 0.2 — Skills + AI Mentor integration

---

## Что было сделано

### 1. Исправлены задания уроков 4 и 5

**Проблема:** Задания не соответствовали контенту уроков.
- Урок 4 (SELECT колонок) → задание было на GROUP BY
- Урок 5 (WHERE + AND) → задание было на JOIN

**Решение:** Задания переписаны под контент:

| Урок | Контент | Новое задание |
|---|---|---|
| 1 | SELECT * | SELECT * FROM materials |
| 2 | Явные колонки | 3 колонки FROM materials |
| 3 | WHERE | active models WHERE status='active' |
| 4 | SELECT колонок | 6 колонок FROM materials |
| 5 | WHERE + AND | fabric AND active FROM materials |

Старые задания (ORDER BY, GROUP BY, JOIN) перенесены в **standalone-задачи** для TaskBook с привязкой к навыкам.

### 2. Seed-loader — upsert-логика

`backend/seed_loader.py`:
- Теперь **обновляет** существующие уроки/задания (раньше только создавал)
- Сравнивает поля title, summary, content_path, expected_answer_sql
- Добавляет/обновляет привязку `task_skills`
- Поддерживает standalone-задачи (lesson_id = NULL)

### 3. Система навыков (Skills)

**Новые таблицы (миграция 0002):**
- `skills` — 10 навыков SQL (select_basic..date_func)
- `student_skills` — прогресс студента по каждому навыку (percentage, confidence, attempts)
- `task_skills` — связь задач с навыками (many-to-many)

**10 навыков:**

| Code | Title | Category |
|---|---|---|
| select_basic | Базовый SELECT | basic |
| where_filter | Фильтрация WHERE | basic |
| order_limit | Сортировка и LIMIT | basic |
| group_by | Агрегация GROUP BY | intermediate |
| join | JOIN | intermediate |
| subqueries | Подзапросы | advanced |
| window_func | Оконные функции | advanced |
| cte | CTE | advanced |
| null_types | NULL и типы данных | intermediate |
| date_func | Работа с датами | intermediate |

### 4. AI Skill Analyzer (Nemotron 70B)

`backend/app/services/ai_skill_analyzer.py`:
- Интеграция с Nvidia API (build.nvidia.com)
- При проверке задания AI оценивает каждый затронутый навык (0.0-1.0)
- Возвращает: skill_scores, feedback, weak_areas, next_focus
- Fallback-режим при недоступности API

**Важно:** Для работы AI нужен корректный endpoint Nvidia API.
Текущая настройка в `.env`:
```
NVIDIA_API_KEY=nvapi-...
NVIDIA_API_BASE=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
```

Endpoint `integrate.api.nvidia.com/v1` возвращает 404. Нужно уточнить правильный endpoint.

### 5. API endpoints (новые)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/skills` | Список всех навыков |
| GET | `/api/v1/skills/student` | Навыки студента с процентами |
| GET | `/api/v1/tasks?skill=X` | Задачи по навыку (TaskBook) |

**Доработан `POST /tasks/{id}/submit`:**
- После валидации → AI-анализ навыков → обновление student_skills
- Ответ содержит `skill_updates` с оценками навыков

### 6. Frontend — Skills Dashboard

Новая страница `/skills`:
- Карта навыков с прогресс-барами
- Цветовая индикация: красный (<40%), жёлтый (40-70%), зелёный (>70%)
- Фильтрация по категориям (basic/intermediate/advanced)
- Клик по навыку → переход в TaskBook

### 7. Frontend — TaskBook

Новая страница `/tasks?skill=X`:
- Фильтр навыков (кнопки-чипсы)
- Список задач с тегами навыков
- Встроенный Monaco SQL Editor
- Выполнение запросов, просмотр результатов

### 8. UI improvements

- **Lesson.tsx:** Авто-выбор первой задачи (больше не нужно кликать)
- **Lesson.tsx:** Отображение skill_updates после проверки (бейджи навыков)
- **Dashboard.tsx:** Блок «Skills» с топ-5 навыками
- **Layout.tsx:** Навигация → Skills / Lessons / Profile

### 9. Баг-фиксы

- `lesson_id` → nullable в tasks (для standalone-задач)
- `validation_strategy_check` → добавлен 'not_empty'
- `MissingGreenlet` → selectinload для отношений моделей
- `StudentSkill.total_attempts` → инициализация 0
- `Percentage` → Decimal сериализация (string в JSON)

---

## Структура изменённых файлов

### Backend
```
backend/
├── app/
│   ├── api/
│   │   ├── skills.py          ★ NEW — Skills API
│   │   ├── tasks.py           ★ MOD — enhanced submit + /tasks?skill=
│   │   └── main.py            ★ MOD — added skills router
│   ├── models/
│   │   ├── skill.py           ★ NEW — Skill, StudentSkill, TaskSkill
│   │   ├── task.py            ★ MOD — nullable lesson_id, skill_tags relation
│   │   ├── user.py            ★ MOD — skill_progress relation
│   │   └── __init__.py        ★ MOD — export new models
│   ├── schemas/
│   │   ├── skill.py           ★ NEW — Pydantic schemas
│   │   └── __init__.py        ★ MOD — fixed docstring
│   └── services/
│       ├── ai_skill_analyzer.py ★ NEW — Nvidia AI integration
│       └── tasks.py           ★ MOD — selectinload for lesson relation
├── alembic/versions/
│   └── 0002_create_skills.py  ★ NEW — migration for skills tables
├── seed_loader.py             ★ MOD — upsert logic + fixed tasks
├── .env.example               ★ MOD — added NVIDIA settings
├── config.py                  ★ MOD — added NVIDIA config
└── requirements.txt           ★ MOD — added httpx
```

### Frontend
```
frontend/src/
├── pages/
│   ├── Skills.tsx             ★ NEW — Skills Dashboard
│   ├── TaskBook.tsx           ★ NEW — TaskBook with skill filter
│   ├── Lesson.tsx             ★ MOD — auto-select task, skill badges
│   └── Dashboard.tsx          ★ MOD — skills block
├── components/
│   └── Layout.tsx             ★ MOD — Skills nav link
├── types/
│   └── index.ts              ★ MOD — skill types
└── App.tsx                    ★ MOD — Skills + TaskBook routes
```

---

## API Test Results (19/19 passed)

```
  ✓ Health endpoint
  ✓ Lessons list
  ✓ Lesson detail
  ✓ Tasks for lesson
  ✓ Task detail
  ✓ Skills list (10 skills)
  ✓ Student skills (initial, 10 skills)
  ✓ Tasks filtered by skill (where_filter)
  ✓ Sandbox execute (SELECT 1)
  ✓ Sandbox reject DROP
  ✓ Sandbox nonexistent table
  ✓ Submit correct task (with skill analysis)
  ✓ Submit wrong task
  ✓ Student skills updated (percentage > 0)
  ✓ Standalone tasks exist (8 total)
  ✓ Join tasks filtered (1 task)
  ✓ Nonexistent task 404
  ✓ Auth required 401
  ✓ Submission history
```

---

## Known Issues

1. **Nvidia API endpoint** — `integrate.api.nvidia.com/v1/chat/completions` возвращает 404. Нужно уточнить правильный URL для аккаунта. Пока работает fallback-режим (анализ на основе is_correct + weight).
2. **Decimal serialization** — percentage/confidence приходят как string в JSON (особенность Decimal → JSON). На фронте обработано через `Number()`.
3. **Frontend proxy** — Vite проксирует `/api` → `localhost:8001`. Если бэкенд на другом порту — поправить `vite.config.ts`.

---

## Что дальше

1. **Починить Nvidia API** — уточнить endpoint, протестировать AI-анализ с реальной LLM
2. **Добавить больше standalone-задач** в TaskBook (для каждого навыка)
3. **Система повторения** (spaced repetition) — review_queue
4. **Чат с AI Mentor** — mentor_conversations + mentor_messages
5. **Dashboard** — добавить блок «Требует повторения»

---

## V2.1 — Deployment Verification (2026-05-29)

### Перенос кода на сервер
Локальная версия `C:\Users\admin\Documents\AI-Mentor` была подмножеством удалённой. Все файлы skills/tasks уже присутствовали на сервере с идентичным содержанием. Дополнительного копирования не потребовалось.

### Исправления
- **requirements.txt:** Исправлен синтаксис — отсутствовала запятая между `python-dotenv` и `httpx` (было `2.0.0httpx`)

### Результаты тестирования (19/19 passed)
Проведено полное E2E-тестирование API на сервере. Все 19 тестов пройдены.

### Известные проблемы (дополнительно)
4. **Нет pip в venv** — при создании использован `--without-pip`. Установка новых зависимостей требует `apt-get install python3-pip` или пересоздания venv.
5. **Нет CORS middleware** — фронтенд на dev-сервере Vite (порт 5173) не сможет обращаться к API (порт 8001) без CORS-заголовков.
6. **httpx не установлен** — нужен для AI-анализа, т.к. pip отсутствует.

## Анализ и предложения по улучшению

### Критические
1. **CORS** — добавить `CORSMiddleware` с allow_origins для dev (5173) и prod
2. **pip в venv** — пересоздать venv с pip или установить `python3-pip` системно
3. **httpx** — после установки pip, выполнить `pip install httpx`

### Важные
4. **Nvidia API endpoint** — `integrate.api.nvidia.com/v1` возвращает 404. Для API Catalog используйте `https://api.build.nvidia.com/v1`
5. **Мало standalone-задач** — 8 задач на 10 навыков. Для subqueries, window_func, cte, null_types, date_func нет задач.
6. **Decimal -> JSON** — percentage/confidence приходят как string. Использовать `serialize_as_any=True` или кастомный JSON-encoder.

### Средние
7. **Логирование** — в ai_skill_analyzer используется `logger.warning`, но нет базовой конфигурации логгера в main.py
8. **Rate limiting** — нет защиты от спама submit'ов
9. **Таймауты** — httpx client имеет 15s таймаут, нет retry-логики
10. **Seed-данные** — все weight=1.0, нет вариации весов навыков

### Низкие
11. **SECRET_KEY** — в .env `dev-secret-key`, для прода генерировать случайный
12. **Frontend** — на сервере нет production-сборки (`npm run build` не запущен)

---

## V2.2 - Code Review Fixes (2026-05-30)

### Critical
1. Migration 0001: tasks.lesson_id nullable=True
2. Removed duplicate index idx_submissions_submitted_at from migration
3. SQL schema platform_schema_v1.sql: tasks.lesson_id optional

### Medium
4. sandbox.py: WITH (CTE) support in validate_select_only
5. validation.py: sql_result strategy implemented
6. ai_skill_analyzer.py: removed hardcoded student name
7. lessons.py: POST progress uses request body instead of query param
8. config.py: SECRET_KEY validation warning on default value

### Minor
9. seed_loader.py: cleanup old TaskSkill tags on upsert

### Changed files
- backend/alembic/versions/0001_create_all_tables.py
- backend/app/services/sandbox.py
- backend/app/services/validation.py
- backend/app/services/ai_skill_analyzer.py
- backend/app/api/lessons.py
- backend/app/config.py
- backend/seed_loader.py
- database/platform_schema_v1.sql
