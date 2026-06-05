# Backend Implementation Plan — MVP 0.1

> **Дата:** 2026-05-25
> **Основание:** TECH_SPEC_V1.md, platform_schema_v1.sql
> **Стек:** Python 3.12+ / FastAPI 0.115+ / SQLAlchemy 2.0+ / Alembic 1.13+ / PostgreSQL 16

---

## Шаг 1. Инициализация FastAPI проекта

### Цель
Создать каркас backend-приложения: структуру директорий, базовые зависимости, точку входа ASGI, запускаемый сервер.

### Файлы

| Файл | Назначение |
|---|---|
| `backend/requirements.txt` | Все зависимости: fastapi, uvicorn, sqlalchemy, alembic, python-jose, passlib[bcrypt], asyncpg, psycopg2-binary, pydantic-settings |
| `backend/app/__init__.py` | Пакет приложения |
| `backend/app/main.py` | Создание экземпляра FastAPI, подключение lifespan (подключение/отключение БД), регистрация роутеров |
| `backend/app/config.py` | Pydantic BaseSettings: DATABASE_URL, SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS, TRAINING_DATABASE_URL |
| `backend/app/database.py` | Два engine: platform_engine (платформа) и training_engine (учебная БД). Сессии через sessionmaker |
| `backend/Dockerfile` | Python-образ, установка зависимостей, запуск uvicorn |

### Результат
- `uvicorn app.main:app` стартует без ошибок
- `GET /health` возвращает `{"status": "ok"}`
- docker-compose может запустить сервис `backend`

### Критерий готовности
- [ ] `pip install -r requirements.txt` устанавливается без ошибок
- [ ] `uvicorn app.main:app --reload` запускается, `localhost:8000/health` отвечает 200
- [ ] Swagger UI доступен по `localhost:8000/docs`

---

## Шаг 2. Подключение PostgreSQL

### Цель
Настроить два независимых подключения к PostgreSQL:
1. **platform_db** — для таблиц платформы (users, lessons, tasks, submissions, lesson_progress, student_profiles)
2. **training_db** — для учебной БД (chair_models, materials, bom_headers, и т.д.) — read-only, statement_timeout=30s

### Файлы

| Файл | Назначение |
|---|---|
| `backend/app/database.py` | Два асинхронных engine через create_async_engine. Platform engine с правами на запись, training engine с read-only + timeout |
| `backend/app/config.py` | Добавить поля: PLATFORM_DATABASE_URL, TRAINING_DATABASE_URL, TRAINING_STATEMENT_TIMEOUT |
| `backend/app/sandbox.py` | Отдельный сервис для выполнения SQL к training_db. Использует отдельное подключение (не путать с сессией платформы) |

### Результат
- Оба engine создаются при старте и корректно закрываются при shutdown
- Sandbox-запросы к тренировочной БД выполняются с таймаутом
- Запросы к платформенной БД работают в транзакциях

### Критерий готовности
- [ ] `POST /api/v1/sandbox/execute` с `SELECT 1` возвращает результат от training_db
- [ ] Запрос с синтаксической ошибкой возвращает понятный текст ошибки
- [ ] Долгий запрос (> 30s) принудительно прерывается
- [ ] Создание таблиц платформы через platform engine работает (проверяется через Шаг 4)

---

## Шаг 3. SQLAlchemy модели

### Цель
Создать ORM-модели для 6 таблиц платформы: users, student_profiles, lessons, tasks, submissions, lesson_progress.

Каждая модель содержит поля, строго соответствующие `platform_schema_v1.sql` (с учётом исправления имён ограничений):

- **users** — id, email, password_hash, display_name, role, status, created_at, updated_at
- **student_profiles** — id, user_id, learning_goal, current_level, preferred_language, weekly_study_minutes, timezone, created_at, updated_at
- **lessons** — id, module_number, lesson_number, slug, title, module_title, summary, content_path, difficulty, estimated_minutes, status, created_at, updated_at
- **tasks** — id, lesson_id, slug, title, description, instructions, expected_result_text, hint, expected_answer_sql, validation_strategy, difficulty, status, created_at, updated_at
- **submissions** — id, student_id, task_id, attempt_number, sql_text, execution_status, execution_result, error_text, score, feedback, is_correct, started_at, submitted_at, reviewed_at
- **lesson_progress** — id, student_id, lesson_id, status, started_at, completed_at, created_at, updated_at

### Файлы

| Файл | Назначение |
|---|---|
| `backend/app/models/__init__.py` | Импорт всех моделей для Alembic |
| `backend/app/models/user.py` | Users, StudentProfiles |
| `backend/app/models/lesson.py` | Lessons |
| `backend/app/models/task.py` | Tasks |
| `backend/app/models/submission.py` | Submissions, LessonProgress |
| `backend/app/schemas/__init__.py` | Импорт всех Pydantic схем |
| `backend/app/schemas/user.py` | UserCreate, UserRead, UserLogin, TokenResponse |
| `backend/app/schemas/lesson.py` | LessonRead, LessonListRead, LessonProgressUpdate |
| `backend/app/schemas/task.py` | TaskRead, TaskListRead |
| `backend/app/schemas/submission.py` | SubmissionCreate, SubmissionRead, SubmissionHistoryItem |
| `backend/app/schemas/sandbox.py` | SqlExecuteRequest, SqlExecuteResponse, SqlCheckRequest, SqlCheckResponse |

### Результат
- Все 6 моделей описаны с правильными типами, индексами и relationships
- Все Pydantic схемы для запросов/ответов готовы
- Relationships настроены (например, `User.profile`, `Lesson.tasks`, `Task.submissions`)

### Критерий готовности
- [ ] Модели соответствуют колонкам из `platform_schema_v1.sql` (типы, nullable, defaults)
- [ ] Схемы валидируют входящие данные (email формат, длина пароля, диапазон difficulty)
- [ ] `Base.metadata` корректно импортируется Alembic
- [ ] `UserRead` не возвращает `password_hash`

---

## Шаг 4. Alembic миграции

### Цель
Настроить Alembic для автоматической генерации миграций на основе SQLAlchemy моделей. Создать начальную миграцию, которая разворачивает 6 таблиц.

### Файлы

| Файл | Назначение |
|---|---|
| `backend/alembic.ini` | Конфигурация Alembic: sqlalchemy.url = platform_db |
| `backend/alembic/env.py` | Настройка target_metadata = Base.metadata, подключение async engine |
| `backend/alembic/versions/0001_create_all_tables.py` | Начальная миграция: CREATE TABLE для 6 таблиц, индексы |
| `backend/alembic/script.py.mako` | Шаблон для новых миграций |

### Результат
- `alembic upgrade head` создаёт 6 таблиц в platform_db
- `alembic downgrade -1` удаляет последнюю миграцию (откат)
- Seed-данные для 5 уроков с заданиями загружаются отдельным скриптом или через `alembic upgrade` с data_migration

### Критерий готовности
- [ ] `alembic upgrade head` выполняется без ошибок
- [ ] В БД появляются 6 таблиц с правильными колонками и индексами (проверить через `\dt` и `\di`)
- [ ] `alembic downgrade -1` корректно откатывает
- [ ] `alembic history` показывает одну миграцию
- [ ] Seed-скрипт заполняет 5 уроков из `lessons/lesson_01.md` — `lessons/lesson_05.md` с соответствующими заданиями

---

## Шаг 5. JWT авторизация

### Цель
Реализовать регистрацию, вход и проверку JWT-токена. Middleware проверяет токен на защищённых маршрутах.

### Файлы

| Файл | Назначение |
|---|---|
| `backend/app/services/auth.py` | Функции: hash_password, verify_password, create_access_token, decode_access_token, get_current_user |
| `backend/app/api/auth.py` | Роутер: POST /register, POST /login, POST /logout, GET /me |
| `backend/app/middleware.py` | Dependency `require_auth` (проверяет Bearer token, возвращает User), опционально `require_admin` |

### Детали реализации

| Endpoint | Описание |
|---|---|
| `POST /api/v1/auth/register` | Принимает email, пароль, display_name. Создаёт пользователя + student_profile. Возвращает JWT |
| `POST /api/v1/auth/login` | Принимает email, пароль. Проверяет hash. Возвращает JWT (24h) |
| `POST /api/v1/auth/logout` | Помечает токен в чёрный список (опционально — для MVP можно игнорировать) |
| `GET /api/v1/auth/me` | Возвращает текущего пользователя (id, email, display_name, role) |

### Результат
- Пользователь может зарегистрироваться, войти и получить JWT
- JWT проверяется на защищённых маршрутах
- Пароль хранится в bcrypt-хэше

### Критерий готовности
- [ ] `POST /register` создаёт пользователя и возвращает токен (проверить через curl)
- [ ] `POST /login` с правильным паролем возвращает токен
- [ ] `POST /login` с неверным паролем возвращает 401
- [ ] `GET /me` с токеном возвращает данные пользователя
- [ ] `GET /me` без токена возвращает 401
- [ ] `GET /me` с битым токеном возвращает 401
- [ ] Пароль в БД хранится в виде bcrypt-хэша (начинается с `$2b$`)

---

## Шаг 6. Lessons API

### Цель
Реализовать endpoint's для получения списка уроков, контента урока и отметки прогресса.

### Файлы

| Файл | Назначение |
|---|---|
| `backend/app/api/lessons.py` | Роутер: GET /lessons, GET /lessons/{slug}, POST /lessons/{slug}/progress |
| `backend/app/services/lessons.py` | Бизнес-логика: получить список с прогрессом пользователя, прочитать Markdown-файл, отметить урок пройденным |

### Endpoint's

| Endpoint | Описание |
|---|---|
| `GET /api/v1/lessons` | Список всех уроков (module_number, lesson_number, slug, title, status ученика). Сортировка по module_number, lesson_number. |
| `GET /api/v1/lessons/{slug}` | Контент урока + метаданные. Markdown читается из файла lessons/{content_path} |
| `POST /api/v1/lessons/{slug}/progress` | Отметить урок как `completed`. Создать или обновить строку в `lesson_progress`. Проверить, что все задания урока выполнены (опционально — для MVP можно отмечать вручную) |

### Детали реализации

- `GET /lessons` должен возвращать прогресс текущего пользователя (LEFT JOIN с lesson_progress)
- `GET /lessons/{slug}` читает Markdown-файл, а не хранит контент в БД
- `POST /lessons/{slug}/progress` — идемпотентный: повторный вызов не создаёт дубликат (upsert по `student_lesson_unique`)

### Результат
- Студент видит список всех 50 уроков с отметками: пройден / не пройден
- Студент может открыть любой урок и прочитать контент
- Студент может отметить урок пройденным

### Критерий готовности
- [ ] `GET /lessons` возвращает массив уроков, каждый с полем `status` ("not_started", "in_progress", "completed", "skipped")
- [ ] `GET /lessons` пустого пользователя (без lesson_progress) показывает все уроки как "not_started"
- [ ] `GET /lessons/lesson-01` возвращает Markdown-контент урока + title, module_title
- [ ] `GET /lessons/lesson-99` (несуществующий) возвращает 404
- [ ] `POST /lessons/lesson-01/progress` создаёт запись в lesson_progress со статусом "completed"
- [ ] Повторный `POST /lessons/lesson-01/progress` не создаёт дубликат (upsert)

---

## Шаг 7. Tasks API + Sandbox

### Цель
Реализовать endpoint's для получения заданий, выполнения SQL в песочнице и отправки на проверку.

### Файлы

| Файл | Назначение |
|---|---|
| `backend/app/api/tasks.py` | Роутер: GET /lessons/{slug}/tasks, GET /tasks/{id}, POST /tasks/{id}/submit, GET /tasks/{id}/submissions |
| `backend/app/api/sandbox.py` | Роутер: POST /sandbox/execute, POST /sandbox/check |
| `backend/app/services/sandbox.py` | Выполнение SQL в training_db: выполнить запрос, перехватить ошибки, вернуть columns + rows |
| `backend/app/services/validation.py` | Стратегии проверки: exact_match (сравнить колонки + значения), sql_result (выполнить эталон и сравнить) |

### Endpoint's

| Endpoint | Описание |
|---|---|
| `GET /api/v1/lessons/{slug}/tasks` | Список заданий для урока (обычно 1). Возвращает id, title, difficulty |
| `GET /api/v1/tasks/{id}` | Полные данные задания: description, instructions, expected_result_text, hint (без expected_answer_sql) |
| `POST /api/v1/sandbox/execute` | Выполнить произвольный SELECT. Принимает sql, возвращает columns + rows + row_count + execution_time_ms |
| `POST /api/v1/sandbox/check` | Выполнить запрос студента и сравнить с эталоном. Принимает task_id + sql, возвращает is_correct + match_type + differences |
| `POST /api/v1/tasks/{id}/submit` | Отправить запрос на проверку. Создаёт submission, выполняет sandbox/check, сохраняет результат |
| `GET /api/v1/tasks/{id}/submissions` | История попыток студента по заданию (attempt_number, status, is_correct, submitted_at) |

### Детали реализации sandbox

- **Безопасность:** только SELECT-запросы. Запрещены: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE. Проверка через парсинг первого токена
- **Таймаут:** `SET statement_timeout = '30s'` перед каждым запросом
- **Лимит строк:** максимум 1000 строк в ответе (добавить `LIMIT 1000`, если нет своего LIMIT)
- **Ошибки:** перехватывать исключения psycopg2, возвращать человекочитаемое сообщение с кодом ошибки
- **Формат ответа:** `{"columns": ["col1", "col2"], "rows": [[val1, val2], ...], "row_count": N, "execution_time_ms": 34}`

### Стратегия exact_match

1. Выполнить запрос студента → `result_student`
2. Выполнить `task.expected_answer_sql` → `result_expected`
3. Сравнить: колонки (имена + порядок), количество строк, значения в каждой ячейке
4. Если совпадает → `is_correct: true`
5. Если не совпадает → `is_correct: false` + `differences: ["row 3: column 'price' expected 1250.50, got 1250.00"]`

### Критерий готовности
- [ ] `GET /lessons/lesson-01/tasks` возвращает массив с 1 заданием
- [ ] `GET /tasks/{id}` возвращает условие задачи, но НЕ показывает expected_answer_sql
- [ ] `POST /sandbox/execute` с `SELECT 1` возвращает columns=["1"], rows=[[1]]
- [ ] `POST /sandbox/execute` с `SELECT * FROM nonexistent` возвращает ошибку с понятным текстом
- [ ] `POST /sandbox/execute` с `INSERT INTO` возвращает ошибку "Only SELECT queries are allowed"
- [ ] `POST /sandbox/check` с правильным запросом возвращает `is_correct: true`
- [ ] `POST /sandbox/check` с неправильным запросом возвращает `is_correct: false` + расхождения
- [ ] `POST /tasks/{id}/submit` создаёт новую строку в submissions
- [ ] `GET /tasks/{id}/submissions` возвращает историю попыток, отсортированную по submitted_at DESC

---

## Итоговая последовательность шагов

```text
Шаг 1: FastAPI каркас        → uvicorn стартует, /health отвечает
    ↓
Шаг 2: PostgreSQL            → два engine, sandbox выполняет SELECT 1
    ↓
Шаг 3: SQLAlchemy модели     → 6 моделей + Pydantic схемы
    ↓
Шаг 4: Alembic миграции      → 6 таблиц созданы, seed 5 уроков
    ↓
Шаг 5: JWT авторизация      → регистрация, вход, защита маршрутов
    ↓
Шаг 6: Lessons API           → список уроков, контент, прогресс
    ↓
Шаг 7: Tasks API + Sandbox   → задания, SQL песочница, проверка
```

Каждый шаг опирается на предыдущий. Шаги 1-5 можно выполнять параллельно с frontend (по API-контракту).

## Что НЕ входит в 7 шагов (намеренно)

- **AI Mentor фидбек** — v1.1
- **Система повторения** — v1.2
- **Адаптивный roadmap** — v1.3
- **Seed всех 50 уроков** — на старте 5 уроков, остальные добавляются по мере готовности
