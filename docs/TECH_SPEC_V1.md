# Tech Spec V1 — MVP 0.1

> **Дата:** 2026-05-25
> **Цель:** За 2 недели получить работающую веб-платформу: урок → SQL → проверка
> **Основание:** docs/MVP_LEARNING_PLATFORM.md

---

## 1. Принципы MVP 0.1

1. **Минимум страниц** — только те, без которых нельзя пройти урок.
2. **Минимум API** — только CRUD для уроков и выполнения SQL.
3. **Минимум таблиц** — только хранение пользователя, урока, попытки.
4. **Никакого AI Mentor** — проверка только точным сравнением.
5. **Никаких навыков, roadmap, повторения** — всё в следующую версию.
6. **Одна команда запуска** — `docker compose up`.

MVP 0.1 — это минимально жизнеспособная платформа, в которой Руслан может:
- зарегистрироваться и войти;
- увидеть список уроков и свой прогресс;
- открыть урок и прочитать контент;
- открыть задание и написать SQL;
- выполнить SQL в песочнице и увидеть результат;
- отправить запрос на проверку и получить «верно/неверно»;
- увидеть, какие уроки уже пройдены.

---

## 2. Страницы (Frontend)

### 2.1. Список страниц MVP 0.1

| № | Страница | URL | Назначение |
|---|---|---|---|
| 1 | Вход | /login | Форма входа (email + пароль) |
| 2 | Регистрация | /register | Форма регистрации |
| 3 | Dashboard | /dashboard | Главная: прогресс, следующий урок, кнопка выхода |
| 4 | Урок | /lessons/{slug} | Контент урока (Markdown) |
| 5 | Задание | /tasks/{id} | Условие задания + встроенный SQL Sandbox |
| 6 | 404 | — | Страница не найдена |

### 2.2. Dashboard

Блоки на странице:
- **Приветствие:** «Руслан, добро пожаловать!»
- **Прогресс:** «Пройдено X из 50 уроков» + прогресс-бар.
- **Следующий урок:** кнопка «Продолжить» — ведёт на первый непройденный урок.
- **Список уроков:** таблица или карточки: номер, название, статус (пройден/не пройден).
- **Кнопка выхода** из системы.

### 2.3. Страница урока

- Заголовок: номер урока, название, модуль.
- Контент: полный Markdown-текст урока (все 12 разделов).
- SQL-блоки: выделены, с подсветкой синтаксиса.
- Кнопка внизу: «Перейти к заданию» → ведёт на страницу задания.
- Навигация: «Предыдущий урок», «Следующий урок», «На главную».

### 2.4. Страница задания (с встроенным SQL Sandbox)

Верхняя половина:
- Условие задания (текст из задачи).
- Ожидаемый результат (текстом).
- SQL-подсказка (если есть).

Нижняя половина (Sandbox):
- Редактор SQL (многострочный, моноширинный, с подсветкой).
- Кнопка «Выполнить» (Ctrl+Enter) — выполняет запрос в песочнице.
- Результат выполнения: таблица со строками и колонками.
- Счётчик строк.
- Сообщение об ошибке (если запрос не выполнился).
- Кнопка «Отправить на проверку» — появляется после успешного выполнения.
- Результат проверки: зелёный баннер «Задание выполнено!» или красный «Есть ошибки».

После успешной проверки на странице появляется кнопка «Вернуться к урокам».

---

## 3. API (Backend)

### 3.1. Группы эндпоинтов MVP 0.1

#### Auth

| Метод | Путь | Описание |
|---|---|---|
| POST | /api/v1/auth/register | Создать пользователя (email, пароль, имя) |
| POST | /api/v1/auth/login | Вход, возвращает JWT |
| POST | /api/v1/auth/logout | Инвалидировать токен |
| GET | /api/v1/auth/me | Данные текущего пользователя |

#### Lessons

| Метод | Путь | Описание |
|---|---|---|
| GET | /api/v1/lessons | Список всех уроков (номер, название, статус ученика) |
| GET | /api/v1/lessons/{slug} | Контент урока (Markdown-текст + метаданные) |
| POST | /api/v1/lessons/{slug}/progress | Отметить урок как пройденный |

#### Tasks

| Метод | Путь | Описание |
|---|---|---|
| GET | /api/v1/lessons/{slug}/tasks | Список заданий для урока (обычно 1) |
| GET | /api/v1/tasks/{id} | Детали задания (условие, ожидаемый результат, подсказка) |

#### Sandbox

| Метод | Путь | Описание |
|---|---|---|
| POST | /api/v1/sandbox/execute | Выполнить SQL-запрос, вернуть результат |
| POST | /api/v1/sandbox/check | Выполнить запрос и сравнить с эталоном |

#### Submissions

| Метод | Путь | Описание |
|---|---|---|
| POST | /api/v1/tasks/{id}/submit | Отправить запрос на проверку |
| GET | /api/v1/tasks/{id}/submissions | История попыток по заданию |

### 3.2. Формат ответов

Единый JSON-формат:

**Успех:**
```json
{
  "data": { ... }
}
```

**Ошибка:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Понятное описание на русском"
  }
}
```

### 3.3. Аутентификация

- JWT (access token, 24 часа — для MVP можно дольше, чтобы не делать refresh).
- Токен передаётся в заголовке `Authorization: Bearer <token>`.
- Пароль хэшируется (bcrypt или passlib).

### 3.4. Sandbox endpoint (ключевой)

**POST /api/v1/sandbox/execute**

Request:
```json
{
  "sql": "SELECT * FROM chair_models WHERE status = 'active';"
}
```

Response (успех):
```json
{
  "data": {
    "columns": ["model_code", "model_name", "status"],
    "rows": [
      ["CH-OP-100", "Операторское кресло Старт", "active"],
      ["CH-MG-300", "Кресло руководителя Престиж", "active"]
    ],
    "row_count": 2,
    "execution_time_ms": 34
  }
}
```

Response (ошибка):
```json
{
  "error": {
    "code": "SYNTAX_ERROR",
    "message": "Ошибка в запросе: column \"statuss\" does not exist",
    "details": {
      "position": 45,
      "hint": "Возможно, вы имели в виду: status"
    }
  }
}
```

**POST /api/v1/sandbox/check**

Request:
```json
{
  "task_id": "uuid",
  "sql": "SELECT model_code, model_name FROM chair_models WHERE status = 'active';"
}
```

Response:
```json
{
  "data": {
    "is_correct": true,
    "match_type": "exact",
    "differences": []
  }
}
```

---

## 4. Таблицы БД

### 4.1. Таблицы, которые нужны в MVP 0.1

#### users
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
email           text NOT NULL UNIQUE
password_hash   text NOT NULL
display_name    text NOT NULL
role            text NOT NULL DEFAULT 'student'
status          text NOT NULL DEFAULT 'active'
created_at      timestamptz NOT NULL DEFAULT now()
updated_at      timestamptz NOT NULL DEFAULT now()
```

#### student_profiles
```sql
id                    UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id               UUID NOT NULL UNIQUE REFERENCES users(id)
learning_goal         text
current_level         text NOT NULL DEFAULT 'beginner'
preferred_language    text NOT NULL DEFAULT 'ru'
created_at            timestamptz NOT NULL DEFAULT now()
```

#### lessons
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
module_number   int NOT NULL
lesson_number   int NOT NULL
slug            text NOT NULL UNIQUE
title           text NOT NULL
module_title    text NOT NULL
summary         text NOT NULL
content_path    text NOT NULL
difficulty      int NOT NULL DEFAULT 1
estimated_minutes int NOT NULL DEFAULT 15
status          text NOT NULL DEFAULT 'published'
created_at      timestamptz NOT NULL DEFAULT now()
UNIQUE (module_number, lesson_number)
```

#### tasks
```sql
id                    UUID PRIMARY KEY DEFAULT gen_random_uuid()
lesson_id             UUID NOT NULL REFERENCES lessons(id)
slug                  text NOT NULL UNIQUE
title                 text NOT NULL
description           text NOT NULL
instructions          text NOT NULL
expected_result_text  text
hint                  text
expected_answer_sql   text NOT NULL
validation_strategy   text NOT NULL DEFAULT 'exact_match'
difficulty            int NOT NULL DEFAULT 1
status                text NOT NULL DEFAULT 'published'
created_at            timestamptz NOT NULL DEFAULT now()
```

#### submissions
```sql
id                    UUID PRIMARY KEY DEFAULT gen_random_uuid()
student_id            UUID NOT NULL REFERENCES users(id)
task_id               UUID NOT NULL REFERENCES tasks(id)
attempt_number        int NOT NULL
sql_text              text NOT NULL
execution_status      text NOT NULL DEFAULT 'submitted'
execution_result      jsonb
error_text            text
score                 numeric(4,3)
feedback              text
is_correct            boolean
started_at            timestamptz NOT NULL DEFAULT now()
submitted_at          timestamptz NOT NULL DEFAULT now()
reviewed_at           timestamptz
```

#### lesson_progress
```sql
id                    UUID PRIMARY KEY DEFAULT gen_random_uuid()
student_id            UUID NOT NULL REFERENCES users(id)
lesson_id             UUID NOT NULL REFERENCES lessons(id)
status                text NOT NULL DEFAULT 'not_started'
started_at            timestamptz
completed_at          timestamptz
UNIQUE (student_id, lesson_id)
```

### 4.2. Таблицы, которые НЕ нужны в MVP 0.1

| Таблица | Нужна в версии | Причина исключения |
|---|---|---|
| skills | v1.1 | Навыки будут добавлены после того, как заработает базовая проверка |
| student_skills | v1.1 | Зависит от skills |
| task_skills | v1.1 | Зависит от skills |
| roadmaps | v1.3 | Адаптивный roadmap — будущая версия |
| roadmap_steps | v1.3 | Зависит от roadmaps |
| mentor_conversations | v1.1 | AI Mentor — следующая версия |
| mentor_messages | v1.1 | Зависит от mentor_conversations |
| review_queue | v1.2 | Система повторения — после аналитики |
| lesson_prerequisites | v1.3 | Пока уроки идут последовательно |

**Итого для MVP 0.1: 6 таблиц** (users, student_profiles, lessons, tasks, submissions, lesson_progress).

---

## 5. Последовательность разработки

### 5.1. День 1-2: Backend основа

1. Инициализировать FastAPI проект.
2. Настроить подключение к основной БД (учебная БД) и платформенной БД.
3. Реализовать модели SQLAlchemy для 6 таблиц (см. раздел 4.1).
4. Реализовать миграции (Alembic).
5. Реализовать auth: регистрация, вход, JWT, middleware.

**Результат:** сервер запускается, можно зарегистрироваться и войти.

### 5.2. День 3-4: CRUD уроков и заданий

1. API: список уроков с прогрессом ученика.
2. API: контент урока (читать Markdown из lessons/).
3. API: список заданий для урока.
4. API: детали задания.
5. Seed: загрузить 5 уроков (lesson_01 — lesson_05) с заданиями в БД.

**Результат:** можно получить список уроков, открыть урок, увидеть задание.

### 5.3. День 5-7: SQL Sandbox

1. Настроить read-only подключение к учебной БД (отдельный пользователь, `statement_timeout = 30s`, max_rows = 1000).
2. Реализовать `POST /sandbox/execute`:
   - выполнить запрос;
   - вернуть колонки + строки;
   - перехватить ошибки и вернуть понятное сообщение.
3. Реализовать `POST /sandbox/check`:
   - выполнить запрос ученика;
   - выполнить эталонный запрос;
   - сравнить результаты (колонки, типы, значения);
   - вернуть is_correct + расхождения.

**Результат:** можно написать SQL, выполнить в песочнице, отправить на проверку.

### 5.4. День 8-10: Frontend основа + страницы

1. Инициализировать React-проект (Vite + TypeScript).
2. Настроить маршрутизацию (react-router): /login, /register, /dashboard, /lessons/:slug, /tasks/:id.
3. Реализовать компоненты:
   - LoginPage + RegisterPage (формы).
   - DashboardPage (прогресс, список уроков).
   - LessonPage (рендер Markdown, подсветка SQL).
   - TaskPage (условие + Sandbox).
4. Подключить API (axios или fetch).
5. Хранить JWT в localStorage.

**Результат:** все страницы выглядят как веб-приложение, но без sandbox-функциональности.

### 5.5. День 11-13: SQL Sandbox в браузере

1. Реализовать компонент SqlEditor (textarea + подсветка синтаксиса через CodeMirror или Monaco).
2. Кнопка «Выполнить»: вызов POST /sandbox/execute, отображение таблицы результата.
3. Кнопка «Отправить на проверку»: вызов POST /tasks/{id}/submit.
4. Отображение результата проверки (зелёный/красный баннер).
5. Компонент SubmissionHistory (список всех попыток по заданию).

**Результат:** можно пройти полный цикл — урок → задание → SQL → проверка.

### 5.6. День 14: Интеграция и полировка

1. Связать страницу урока со страницей задания (кнопка «Перейти к заданию»).
2. После успешной проверки отмечать урок как пройденный.
3. Dashboard показывает актуальный прогресс.
4. Последовательная навигация: следующий урок открывается после прохождения текущего.
5. Docker Compose: backend + frontend + nginx (или CORS для разработки).

**Результат:** первый рабочий релиз.

---

## 6. Первая неделя (дни 1-7)

**Цель:** готовый backend + SQL Sandbox, можно проверить через curl/Postman.

### Что должно работать к концу дня 7:

1. **Регистрация и вход.**
   - `POST /api/v1/auth/register` — создать пользователя.
   - `POST /api/v1/auth/login` — получить JWT.
   - `GET /api/v1/auth/me` — данные пользователя.

2. **Уроки.**
   - `GET /api/v1/lessons` — список с прогрессом.
   - `GET /api/v1/lessons/lesson-01` — контент урока.
   - `POST /api/v1/lessons/lesson-01/progress` — отметить пройденным.

3. **Задания.**
   - `GET /api/v1/lessons/lesson-01/tasks` — список заданий урока.
   - `GET /api/v1/tasks/{id}` — детали задания.

4. **SQL Sandbox.**
   - `POST /api/v1/sandbox/execute` — выполнить любой SELECT.
   - `POST /api/v1/sandbox/check` — выполнить и проверить.

5. **Submissions.**
   - `POST /api/v1/tasks/{id}/submit` — отправить на проверку.
   - `GET /api/v1/tasks/{id}/submissions` — история попыток.

6. **База данных.** 6 таблиц созданы, 5 уроков и заданий загружены seed-ами.

### Критерий готовности первой недели:

Можно выполнить полный сценарий через curl:
1. Зарегистрироваться.
2. Получить список уроков.
3. Открыть урок.
4. Получить задание.
5. Написать SQL и выполнить в песочнице.
6. Отправить на проверку.
7. Получить «верно» или «неверно».

---

## 7. Вторая неделя (дни 8-14)

**Цель:** готовый frontend + полный пользовательский сценарий в браузере.

### Что должно работать к концу дня 14:

1. **Frontend: страницы.**
   - `/login` — вход.
   - `/register` — регистрация.
   - `/dashboard` — прогресс, список уроков, следующий урок.
   - `/lessons/{slug}` — контент урока с Markdown и подсветкой SQL.
   - `/tasks/{id}` — задание + SQL Sandbox.

2. **SQL Sandbox в браузере.**
   - Редактор SQL с подсветкой.
   - Выполнение запроса, отображение результата.
   - Отправка на проверку.
   - Отображение результата проверки.

3. **Навигация.**
   - С главной → на следующий урок.
   - С урока → на задание.
   - С задания → назад к урокам (после успешной проверки).
   - Кнопка «Выход».

4. **Docker.**
   - `docker compose up` запускает всё: БД, backend, frontend.

### Критерий готовности второй недели:

Любой человек с нулевым опытом может:
1. Открыть браузер по URL.
2. Зарегистрироваться (или войти, если уже есть учётка).
3. Увидеть список уроков.
4. Кликнуть на первый урок.
5. Прочитать теорию.
6. Нажать «Перейти к заданию».
7. Написать SQL-запрос.
8. Нажать «Выполнить» и увидеть результат.
9. Нажать «Отправить на проверку».
10. Увидеть зелёный баннер «Задание выполнено!».
11. Вернуться на главную и увидеть прогресс 1/50.

---

## 8. Первый рабочий релиз

### Критерии Definition of Done

**Backend:**
- [x] FastAPI запускается, все эндпоинты отвечают.
- [x] Auth работает: регистрация, вход, JWT.
- [x] SQL Sandbox выполняет запросы к учебной БД.
- [x] Проверка сравнивает результат ученика с эталоном.
- [x] Все попытки сохраняются в submissions.
- [x] Прогресс по урокам сохраняется в lesson_progress.
- [x] 5 seed-уроков с заданиями загружены.

**Frontend:**
- [x] 6 страниц работают: login, register, dashboard, lesson, task, 404.
- [x] Dashboard показывает прогресс.
- [x] Markdown-контент урока отображается корректно.
- [x] SQL Sandbox с редактором и кнопкой «Выполнить».
- [x] Результат выполнения отображается как таблица.
- [x] Кнопка «Отправить на проверку» работает.
- [x] Результат проверки отображается (зелёный/красный).
- [x] Навигация между страницами работает.

**Инфраструктура:**
- [x] Docker Compose: одна команда `docker compose up`.
- [x] Учебная БД разворачивается с seed-данными.
- [x] Frontend доступен по HTTP.
- [x] Backend доступен по HTTP для frontend.

### Что НЕ входит в первый релиз (намеренно)

| Функция | Версия |
|---|---|
| AI Mentor feedback | v1.1 |
| Карта навыков | v1.1 |
| Список навыков (skills, student_skills) | v1.1 |
| Чат с AI-наставником | v1.1 |
| Система повторения (review_queue) | v1.2 |
| Персональный roadmap | v1.3 |
| Адаптивное обучение | v1.3 |
| n8n-сценарии | v1.1 |
| Экспорт в CSV | v2.0 |
| Визуализация данных | v2.0 |
| Мобильная версия | v2.0 |

### Команда запуска

```bash
git clone <repo>
cd ai-mentor
docker compose up
```

После запуска:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API docs (Swagger): `http://localhost:8000/docs`
- Учебная БД: `localhost:5432` (training)

---

## Приложение: Технологический стек MVP 0.1

| Компонент | Технология | Версия |
|---|---|---|
| Backend | Python + FastAPI | 0.115+ |
| ORM | SQLAlchemy | 2.0+ |
| Миграции | Alembic | 1.13+ |
| Frontend | React + Vite + TypeScript | 18+, 5+, 5+ |
| Маршрутизация | react-router-dom | 6+ |
| HTTP-клиент | axios | 1.7+ |
| Редактор SQL | CodeMirror 6 (vue-codemirror) | 6+ |
| Markdown | react-markdown + rehype-highlight | 9+ |
| База платформы | PostgreSQL 16 | 16 |
| Учебная БД | PostgreSQL 16 (та же или вторая) | 16 |
| Аутентификация | python-jose + passlib[bcrypt] | — |
| Docker | docker compose | 3.8+ |
| CI/CD | GitHub Actions (линтер + тесты) | — |

### Структура директорий

```
ai-mentor/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── lesson.py
│   │   │   ├── task.py
│   │   │   └── submission.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── lesson.py
│   │   │   ├── task.py
│   │   │   └── submission.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── lessons.py
│   │   │   ├── tasks.py
│   │   │   ├── sandbox.py
│   │   │   └── submissions.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── sandbox.py
│   │   │   └── validation.py
│   │   └── middleware.py
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── LessonPage.tsx
│   │   │   └── TaskPage.tsx
│   │   ├── components/
│   │   │   ├── SqlEditor.tsx
│   │   │   ├── SqlResult.tsx
│   │   │   ├── LessonContent.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── LessonList.tsx
│   │   │   ├── TaskDescription.tsx
│   │   │   └── SubmissionHistory.tsx
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── lessons.ts
│   │   │   └── tasks.ts
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── lessons/
│   ├── lesson_01.md
│   ├── lesson_02.md
│   └── ...
├── database/
│   ├── training_schema.sql
│   ├── seed_training_data.sql
│   └── seed_platform_data.sql
├── docker-compose.yml
└── README.md
```