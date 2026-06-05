# HANDOFF — Фаза 2: Skills & Analytics + Mistakes System

> **Дата:** 2026-06-03
> **Проект:** AI-Mentor Platform
> **Основание:** Feature Phase A (v1.1)

---

## 1. Что сделано

| Компонент | Описание | Файлы | Статус |
|---|---|---|---|
| AI Skill Analyzer | Интегрирован и протестирован (был реализован ранее, добавлена интеграция с mistakes) | `services/ai_skill_analyzer.py` | ✅ Verified |
| Mistakes system | Полная система типовых ошибок: модель, миграция, API, детекция | `models/mistake.py`, `schemas/mistake.py`, `api/mistakes.py`, `services/mistakes.py`, `alembic/versions/0003_create_mistakes.py` | ✅ New |
| Mistake detection in submit | При неверном ответе автоматически детектируются типовые ошибки | `api/tasks.py` (изменён) | ✅ Updated |
| Mistake detection in sandbox | При ошибке выполнения SQL тоже детектируются ошибки | `api/sandbox.py` (изменён) | ✅ Updated |
| Skills LEFT JOIN | Оптимизирован запрос получения навыков студента | `api/skills.py` (изменён в фазе 1) | ✅ Done |

---

## 2. Новые таблицы БД

### mistake_types

| Поле | Тип | Описание |
|---|---|---|
| id | UUID PK | Идентификатор |
| code | VARCHAR(100) UNIQUE | Машинный код (напр. `missing_where`) |
| title | TEXT | Название |
| description | TEXT nullable | Описание |
| domain | VARCHAR(50) | Область: `sql`, `analytics`, `product` |
| severity_default | INT 1-5 | Базовая тяжесть |

### student_mistakes

| Поле | Тип | Описание |
|---|---|---|
| id | UUID PK | Идентификатор |
| student_id | UUID FK -> users.id | Студент |
| mistake_type_id | UUID FK -> mistake_types.id | Тип ошибки |
| skill_id | UUID FK -> skills.id nullable | Связанный навык |
| submission_id | UUID FK -> submissions.id nullable | Попытка, где найдена |
| title | TEXT | Описание ошибки |
| details | TEXT nullable | Подробности |
| severity | INT 1-5 | Тяжесть |
| repeat_count | INT | Сколько раз повторялась |
| status | VARCHAR(20) | `new`, `active`, `training`, `resolved`, `ignored` |
| first_seen_at | TIMESTAMPTZ | Первое появление |
| last_seen_at | TIMESTAMPTZ | Последнее появление |
| resolved_at | TIMESTAMPTZ nullable | Дата закрытия |

---

## 3. Новые API эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/v1/mistakes/types` | Список всех типов ошибок |
| GET | `/api/v1/mistakes` | Ошибки текущего студента (опционально `?status=active`) |
| POST | `/api/v1/mistakes/resolve?skill_code=xxx` | Закрыть ошибки по навыку |
| POST | `/api/v1/mistakes/seed` | Создать недостающие типы ошибок |

---

## 4. Типы ошибок (детектируемые паттерны)

| Код | Описание | Логика |
|---|---|---|
| `missing_where` | Отсутствует WHERE | Запрос начинается с SELECT/DELETE/UPDATE и нет WHERE |
| `select_star` | SELECT * вместо колонок | `select *` в lowercase |
| `missing_join_condition` | JOIN без ON | Есть JOIN, нет ON/USING |
| `typo_in_column` | Опечатка в имени | Определяется по ошибке БД (does not exist) |

**Правила эскалации:**
- repeat_count < 3: статус `new`, severity не повышается
- repeat_count >= 3: статус `active`, severity +1
- repeat_count >= 5: статус `training`

---

## 5. Миграция

```bash
cd backend
alembic upgrade head
# Инициализация типов ошибок:
curl -X POST http://localhost:8000/api/v1/mistakes/seed
```

---

## 6. Проверка

```bash
# Получить типы ошибок
curl http://localhost:8000/api/v1/mistakes/types \
  -H "Authorization: Bearer $TOKEN"

# Создать типы
curl -X POST http://localhost:8000/api/v1/mistakes/seed

# Ошибки студента
curl http://localhost:8000/api/v1/mistakes \
  -H "Authorization: Bearer $TOKEN"

# Закрыть ошибки по навыку
curl -X POST "http://localhost:8000/api/v1/mistakes/resolve?skill_code=select_basic" \
  -H "Authorization: Bearer $TOKEN"
```

---

*Document created: June 3, 2026*
*AI Mentor Development Team*