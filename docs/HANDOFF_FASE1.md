# HANDOFF — Фаза 1: Исправление багов и улучшение безопасности

> **Дата:** 2026-06-03
> **Проект:** AI-Mentor Platform
> **Основание:** Code review Phase 1 (Critical + High + Medium priority bugs)

---

## 1. Список исправлений

| ID | Приоритет | Описание | Файлы | Статус |
|---|---|---|---|---|
| S1 | **Критический** | SECRET_KEY: падение при старте вместо предупреждения | `config.py` | ✅ Fixed |
| B2 | **Высокий** | submit_task: улучшена обработка ошибок SQL (score, reviewed_at) | `api/tasks.py` | ✅ Fixed |
| B3 | **Высокий** | instructions уже есть в TaskRead — не требуется изменений | `schemas/task.py` | ✅ Verified |
| S2 | **Средний** | sqlparse для проверки SQL-запросов, блокировка DDL/DML внутри CTE | `services/sandbox.py`, `requirements.txt` | ✅ Fixed |
| P1 | **Средний** | LEFT JOIN уроков — индексы уже есть, оптимизация не требуется | `services/lessons.py` | ✅ Verified |
| P2+B6 | **Средний** | skills.py: объединены два запроса в один LEFT JOIN | `api/skills.py` | ✅ Fixed |
| P3 | **Низкий** | Кэширование Markdown-файлов через `functools.lru_cache` | `services/lessons.py` | ✅ Fixed |
| S3 | **Низкий** | CORS вынесен в переменную окружения `CORS_ORIGINS` | `main.py`, `config.py` | ✅ Fixed |

---

## 2. Детали изменений

### S1: SECRET_KEY — принудительное падение при старте

**Файл:** `backend/app/config.py`

**До:** `logging.warning` (можно игнорировать)

**После:** `sys.exit(1)` с сообщением об ошибке:
```
FATAL: SECRET_KEY is set to a default insecure value!
Generate a strong random key with: openssl rand -hex 32
Then set it in your .env file as SECRET_KEY=<generated_key>
```

**Проверка:** сервер не запустится, пока SECRET_KEY не будет изменён.

---

### B2: Улучшена обработка ошибок в submit_task

**Файл:** `backend/app/api/tasks.py`

**Изменения:**
- При ошибке SQL теперь проставляется `sub.score = 0.0`
- Проставляется `sub.reviewed_at = datetime.now(timezone.utc)`
- Улучшено извлечение error_message из `exc.detail`

**Проверка:** после ошибки SQL сабмишен имеет корректные score и reviewed_at.

---

### S2: sqlparse для проверки SQL-запросов

**Файлы:** `backend/app/services/sandbox.py`, `backend/requirements.txt`

**Изменения:**
- Добавлена зависимость `sqlparse>=0.5.0,<1.0.0` в `requirements.txt`
- Полная замена валидации `validate_select_only()`:
  - Вместо ручного парсинга первой лексемы используется `sqlparse`
  - Проверяется `statement.get_type()` для каждого statement
  - Рекурсивная проверка (`_check_forbidden_in_children`) обнаруживает DDL/DML внутри CTE
  - Добавлены новые коды ошибок: `SQL_PARSE_ERROR`, `FORBIDDEN_STATEMENT_IN_CTE`

**Безопасность:**
- Запросы вида `WITH cte AS (INSERT INTO ...) SELECT ...` теперь блокируются
- `REPLACE`, `MERGE`, `LOAD`, `UNLOAD` добавлены в запрещённые

**Проверка:** запросы с DDL/DML в любом положении отклоняются.

---

### P2+B6: Объединение запросов в skills.py

**Файл:** `backend/app/api/skills.py`

**До:** два отдельных запроса (StudentSkill + Skill) → объединение в Python

**После:** один запрос с LEFT JOIN:
```python
SELECT Skill.*, StudentSkill.*
FROM skills
LEFT JOIN student_skills ON skill_id = skills.id AND student_id = :user_id
WHERE is_active = true
ORDER BY sort_order
```

**Результат:** один раунд-трип к БД вместо двух. Навыки без прогресса получают нулевые значения.

**Проверка:** эндпоинт `GET /api/v1/skills/student` возвращает те же данные.

---

### P3: Кэширование Markdown-файлов

**Файл:** `backend/app/services/lessons.py`

**Изменения:**
- Добавлен `functools.lru_cache(maxsize=32)` на `read_lesson_content`
- Внутренняя функция `_read_lesson_file` читает файл с диска
- Кэш сбрасывается при перезапуске сервера

**Результат:** повторные запросы одного урока не читают файл с диска.

---

### S3: CORS в переменную окружения

**Файлы:** `backend/app/main.py`, `backend/app/config.py`

**До:** хардкод `['http://localhost:5173', 'http://localhost:4173']`

**После:** `settings.CORS_ORIGINS` с дефолтным значением `http://localhost:5173,http://localhost:4173`

**В `.env`:**
```env
CORS_ORIGINS=https://n8n-sharipov.ru,https://example.com
```

---

## 3. Новые зависимости

```diff
+ sqlparse>=0.5.0,<1.0.0
```

---

## 4. Новые переменные окружения

```env
CORS_ORIGINS=http://localhost:5173,http://localhost:4173
```

---

## 5. Проверка изменений

### Backend
```bash
cd backend

# Проверка импортов
python -c "from app.services.sandbox import validate_select_only; print('OK')"

# Проверка SECRET_KEY (ожидается падение)
SECRET_KEY=change-me python -c "from app.config import settings"  # должно упасть

# Проверка kэширования
python -c "from app.services.lessons import read_lesson_content; print('OK')"
```

### API тесты
```bash
# Регистрация
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"secret123","display_name":"Test"}'

# Проверка sandbox с запрещённым запросом
TOKEN="<jwt>"
curl -X POST http://localhost:8000/api/v1/sandbox/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql":"INSERT INTO chair_models VALUES (1)"}'
# Ожидается: 400 FORBIDDEN_STATEMENT

# Проверка sandbox с CTE
curl -X POST http://localhost:8000/api/v1/sandbox/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql":"WITH cte AS (SELECT * FROM chair_models) SELECT * FROM cte"}'
# Ожидается: 200 OK с данными
```

---

## 6. План дальнейших работ (Phase B, не вошло в фазу 1)

| Компонент | Описание |
|-----------|----------|
| Skills v1.1 | Интеграция ai_skill_analyzer, таблицы skills уже используются |
| Mistakes | Система типовых ошибок (таблицы mistake_types, student_mistakes) |
| Roadmap | Таблицы roadmaps, roadmap_steps |
| AI Mentor | Чат с контекстом ученика (mentor_conversations, mentor_messages) |
| Docker Compose | Полный compose-файл для одно-командного запуска |
| Tests | Unit + e2e тесты |

---

*Document created: June 3, 2026*
*AI Mentor Development Team*