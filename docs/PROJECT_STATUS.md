# PROJECT_STATUS.md

> **Дата:** 2026-05-25
> **Проект:** AI-Mentor Platform (MVP 0.1)
> **Ветка:** main

---

## Общий статус

| Компонент | Статус | Примечание |
|-----------|--------|------------|
| Backend (FastAPI) | Реализован | Шаг 1-2: каркас + 2 БД |
| SQLAlchemy модели | Реализованы | Шаг 3: 6 моделей |
| Alembic миграции | Реализованы | Шаг 4: 1 миграция (6 таблиц) |
| JWT авторизация | Реализован | Шаг 5: register, login, me, bcrypt, JWT 24h |
| Lessons API | Реализован | Шаг 6: список, контент, прогресс |
| Tasks API + Sandbox | Реализован | Шаг 7: задания, execute, check, submit |

---

## Выполненные шаги

### Шаг 1-2: FastAPI каркас + PostgreSQL

**Файлы:**
```
backend/
├── .env.example          # шаблон настроек
├── requirements.txt      # fastapi, uvicorn, sqlalchemy, asyncpg, alembic, psycopg2-binary
├── Dockerfile            # Python 3.12-slim, uvicorn
└── app/
    ├── __init__.py
    ├── config.py         # Pydantic BaseSettings (загрузка из .env)
    ├── database.py       # два async engine + health check + lifecycle
    └── main.py           # FastAPI app + /health + /health/db
```

**Endpoint'ы:**
- `GET /health` — статус сервиса
- `GET /health/db` — проверка подключения к обеим БД

**Два подключения:**
- `platform_engine` — read-write, pool_size=5, для таблиц платформы
- `training_engine` — read-only, pool_size=2, `statement_timeout=30s`

---

### Шаг 3: SQLAlchemy модели

**Файлы:** `backend/app/models/` (7 файлов)

| Модель | Таблица | Связи |
|--------|---------|-------|
| `User` | `users` | → profile, submissions, lesson_progress_entries |
| `StudentProfile` | `student_profiles` | → user |
| `Lesson` | `lessons` | → tasks, progress_entries |
| `Task` | `tasks` | → lesson, submissions |
| `Submission` | `submissions` | → student, task |
| `LessonProgress` | `lesson_progress` | → student, lesson |

**Особенности:**
- SQLAlchemy 2.0 `Mapped[]` / `mapped_column()`
- `TimestampMixin` с `server_default=func.now()` и `onupdate=func.now()`
- Все `CheckConstraint` с уникальными именами (без конфликтов)
- Partial index: `idx_submissions_is_correct WHERE is_correct IS NOT NULL`
- `Submission` не наследует `TimestampMixin` (нет триггера в SQL)

---

### Шаг 4: Alembic миграции

**Файлы:**
```
backend/
├── alembic.ini                 # конфигурация
└── alembic/
    ├── env.py                  # target_metadata = Base.metadata
    ├── script.py.mako          # шаблон новых миграций
    └── versions/
        ├── __init__.py
        └── 0001_create_all_tables.py   # создание 6 таблиц
```

**Миграция `0001_create_all_tables.py`:**
- Создаёт 6 таблиц в правильном порядке (FK dependency order)
- 8 внешних ключей (CASCADE / RESTRICT)
- 20 CheckConstraint с именованными ограничениями
- 16 индексов (включая 1 partial index)
- `downgrade()` удаляет таблицы в обратном порядке

**Проверено:** `Base.metadata.tables` содержит все 6 таблиц.

---

### Шаг 5: JWT авторизация

**Файлы:**
```
backend/app/
├── schemas/
│   ├── __init__.py
│   └── user.py           # UserCreate, UserLogin, UserRead, TokenResponse
├── services/
│   ├── __init__.py
│   └── auth.py           # hash_password, verify_password, create_access_token, decode_access_token, get_current_user
├── api/
│   ├── __init__.py
│   └── auth.py           # POST /register, POST /login, GET /me
├── middleware.py          # require_active, require_admin
└── main.py               # +auth_router, +exception_handler (единый формат ошибок)
```

**Endpoint'ы:**
| Метод | Путь | Описание |
|---|---|---|
| POST | /api/v1/auth/register | Создать пользователя + profile, вернуть JWT |
| POST | /api/v1/auth/login | Проверить email/пароль, вернуть JWT |
| GET | /api/v1/auth/me | Данные текущего пользователя (требует токен) |

**Детали:**
- `passlib[bcrypt]` + `bcrypt==4.0.1` — хэширование паролей
- `python-jose[cryptography]` — JWT access token (24h)
- Токен передаётся в `Authorization: Bearer <token>`
- При регистрации автоматически создаётся `StudentProfile`
- Единый формат ошибок: `{"error": {"code": "...", "message": "..."}}`
- `require_active` — проверяет статус пользователя (не blocked)
- `require_admin` — проверяет роль admin (задел на будущее)
- Поле `password_hash` никогда не возвращается в API
- `UserRead` использует `model_config = {"from_attributes": True}`

**Проверено:**
- hash_password / verify_password работают (bcrypt, хэш начинается с `$2b$`)
- create_access_token / decode_access_token работают (JWT)
- Все 3 auth-роута зарегистрированы в приложении

---

### Шаг 6: Lessons API

**Файлы:**
```
backend/app/
├── schemas/
│   └── lesson.py           # LessonListItem, LessonDetail, ProgressUpdateResponse
├── services/
│   └── lessons.py          # get_lessons_with_progress, get_lesson_by_slug, read_lesson_content, upsert_progress
├── api/
│   └── lessons.py          # GET /lessons, GET /lessons/{slug}, POST /lessons/{slug}/progress
└── main.py                 # +lessons_router
```

**Endpoint'ы:**
| Метод | Путь | Описание |
|---|---|---|
| GET | /api/v1/lessons | Список уроков со статусом пользователя (LEFT JOIN lesson_progress) |
| GET | /api/v1/lessons/{slug} | Детали урока + Markdown-контент (читается из lessons/*.md) |
| POST | /api/v1/lessons/{slug}/progress | Отметить урок как completed (upsert) |

**Детали:**
- `LESSONS_DIR` вычисляется автоматически относительно `backend/app/config.py` (на 3 уровня вверх → ai-mentor/lessons/)
- LEFT JOIN с `lesson_progress` — если записи нет, статус = `"not_started"`
- `read_lesson_content()` использует `os.path.basename(content_path)` для поддержки разных форматов пути
- `upsert_progress()` — проверяет существование, создаёт или обновляет, проставляет `started_at`/`completed_at`
- Повторный вызов `POST .../progress` не создаёт дубликат (upsert)
- Все эндпоинты требуют JWT (через `require_active`)

**Проверено:**
- Все 3 lessons-роута зарегистрированы в приложении
- `LESSONS_DIR` = `/home/sharipov/projects/ai-mentor/lessons`, директория существует
- `read_lesson_content("lesson_01.md")` читает 11467 байт, первая строка `# Урок 01. Что такое база данных и PostgreSQL`

---

### Шаг 7: Tasks API + SQL Sandbox

**Файлы:**
```
backend/app/
├── schemas/
│   ├── task.py            # TaskListItem, TaskRead (без expected_answer_sql)
│   ├── submission.py      # SubmissionCreate, SubmissionRead, SubmissionHistoryItem
│   └── sandbox.py         # SqlExecuteRequest, SqlExecuteResponse, SqlCheckRequest, SqlCheckResponse
├── services/
│   ├── sandbox.py         # validate_select_only, execute_sql (с LIMIT), execute_sql_for_validation
│   ├── validation.py      # validate_submission (сравнение колонок, строк, значений)
│   └── tasks.py           # get_tasks_for_lesson, get_task_by_id, get_task_with_answer, create_submission, get_submission_history
├── api/
│   ├── tasks.py           # GET /lessons/{slug}/tasks, GET /tasks/{id}, POST /tasks/{id}/submit, GET /tasks/{id}/submissions
│   └── sandbox.py         # POST /sandbox/execute, POST /sandbox/check
└── main.py                # +tasks_router, +sandbox_router
```

**Endpoint'ы:**
| Метод | Путь | Описание |
|---|---|---|
| GET | /api/v1/lessons/{slug}/tasks | Список заданий для урока |
| GET | /api/v1/tasks/{id} | Детали задания (без expected_answer_sql) |
| POST | /api/v1/sandbox/execute | Выполнить SELECT, вернуть columns + rows |
| POST | /api/v1/sandbox/check | Выполнить запрос и сравнить с эталоном |
| POST | /api/v1/tasks/{id}/submit | Отправить на проверку, сохранить попытку |
| GET | /api/v1/tasks/{id}/submissions | История попыток студента |

**Безопасность sandbox:**
- Проверка первого токена: только `SELECT` (пропускает комментарии)
- Запрещены: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, COPY
- `statement_timeout = 30s` (через SET statement_timeout)
- `fetchmany(1000)` — максимум 1000 строк (только execute, не check)
- Все запросы выполняются в `training_db` (read-only по правам пользователя)
- Ошибки PostgreSQL перехватываются и возвращаются с понятным текстом

**Валидация (exact_match):**
1. Выполнить `student_sql` → `student_result`
2. Выполнить `expected_answer_sql` → `expected_result`
3. Сравнить: колонки (имена + порядок), количество строк, значения
4. Если не совпадает — построить список `differences` с указанием строки и колонки
5. `execute_sql_for_validation()` — без LIMIT (точность важнее)
6. `execute_sql()` — с LIMIT 1000 (для sandbox/execute, безопасность)

**Submissions:**
- `attempt_number` = MAX(attempt_number) + 1 для student_id + task_id
- При ошибке SQL: `execution_status = "syntax_error"`, сохраняется error_text
- При успехе: `execution_status = "reviewed"`, проставляется score и reviewed_at

**Проверено:**
- Все 6 эндпоинтов зарегистрированы в приложении (12 API endpoints total)
- Код компилируется без ошибок
- Sandbox корректно обрабатывает ошибки подключения (проверено: InvalidPasswordError → человекочитаемое сообщение)

---

## Команды

### Локальный запуск
```bash
cd backend
cp .env.example .env
# отредактировать .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Миграции
```bash
cd backend
alembic upgrade head    # применить миграции
alembic downgrade -1    # откатить последнюю
alembic history         # история миграций
alembic current         # текущая версия
```

### Проверка
```bash
# Health
curl http://localhost:8000/health
curl http://localhost:8000/health/db

# Auth
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret123","display_name":"Тест"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret123"}'

curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"

# Sandbox — выполнить SELECT
curl -X POST http://localhost:8000/api/v1/sandbox/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT 1 AS num"}'

# Sandbox — проверка
curl -X POST http://localhost:8000/api/v1/sandbox/check \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "<uuid>", "sql": "SELECT 1"}'

# Уроки — список заданий
curl http://localhost:8000/api/v1/lessons/lesson-01/tasks \
  -H "Authorization: Bearer <token>"

# Задания — детали
curl http://localhost:8000/api/v1/tasks/<task_id> \
  -H "Authorization: Bearer <token>"

# Задания — отправить на проверку
curl -X POST http://localhost:8000/api/v1/tasks/<task_id>/submit \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"sql_text": "SELECT * FROM chair_models"}'

# Задания — история попыток
curl http://localhost:8000/api/v1/tasks/<task_id>/submissions \
  -H "Authorization: Bearer <token>"
```