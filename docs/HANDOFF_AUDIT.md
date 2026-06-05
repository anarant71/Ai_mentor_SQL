# Handoff: Аудит и переработка первых 3 уроков

> Дата: 2026-05-27
> Автор: opencode AI

---

## Что было сделано

### 1. Переписаны уроки 1-3 (педагогический flow)

**Проблема:** Задания требовали знаний из следующих уроков. Lesson-02 task требовал WHERE (был в отдельном файле, не подключённом к seed). Lesson-03 task требовал ORDER BY + LIMIT (аналогично).

**Решение:** Последовательность перестроена:

| Урок | Было | Стало |
|------|------|-------|
| 1 | Теория БД (без SQL) + задание SELECT колонок | SELECT * FROM. Задача: получить любые строки из materials |
| 2 | SELECT * FROM + psql + задание WHERE | Явные колонки, SELECT -> FROM. Задача: 3 колонки из materials |
| 3 | Синтаксис SQL + ORDER BY/LIMIT | WHERE. Задача: активные модели с конкретными колонками |

ORDER BY и LIMIT перенесены в урок 4.

**Файлы:** lessons/lesson_01.md, lesson_02.md, lesson_03.md (переписаны)

### 2. Обновлён seed_loader.py

- lesson-01: validation_strategy = not_empty
- lesson-02: validation_strategy = exact_match
- lesson-03: validation_strategy = exact_match

### 3. Улучшен validation.py

- Добавлена стратегия not_empty
- Человеческие сообщения: "Запрос нашёл правильные строки, но SELECT * выводит все колонки..."

### 4. Починен баг прогресса

Не понижать completed -> in_progress (lessons.py:99-101)

### 5. Улучшен Lesson.tsx

- StageSeparator (разделители этапов)
- TaskBlock (блок ЗАДАНИЕ с оранжевой рамкой)
- SqlResultTable (sticky header, striped, UUID truncation)
- Локализация кнопок и сообщений на русский

---

## Файлы проекта (изменённые)

- ai-mentor/lessons/lesson_01.md -- UPDATED
- ai-mentor/lessons/lesson_02.md -- UPDATED
- ai-mentor/lessons/lesson_03.md -- UPDATED
- ai-mentor/backend/seed_loader.py -- UPDATED
- ai-mentor/backend/app/services/validation.py -- UPDATED
- ai-mentor/backend/app/services/lessons.py -- UPDATED
- ai-mentor/backend/app/api/tasks.py -- UPDATED
- ai-mentor/backend/app/api/sandbox.py -- UPDATED
- frontend/src/pages/Lesson.tsx -- UPDATED