# Handoff: Интеграция карты сильных и слабых сторон

> Дата: 2026-06-05
> Автор: opencode AI

---

## Что было сделано

Реализована карта сильных и слабых сторон ученика на фронтенде. Аналитика считается целиком на клиенте (без лишнего API-запроса).

### 1. Frontend: типы (`types/index.ts`)

- В `StudentSkill` добавлено поле `last_practiced_at: string | null`
- Добавлен интерфейс `SkillAnalysis` с полями:
  - `overall_level`, `level_label` — общий уровень
  - `studied_count` — сколько навыков изучено
  - `strong`, `weak`, `fading`, `unstudied` — классифицированные массивы

### 2. Dashboard (`pages/Dashboard.tsx`)

Добавлены новые блоки (сверху вниз):

| Блок | Детали |
|---|---|
| **Your level** | Общий уровень (beginner/junior/middle/strong_middle/advanced), progress-bar, счётчики strong/weak/unstudied |
| **Needs practice** | Навыки с percentage < 40%. Карточки с красным фоном, ссылка на TaskBook с фильтром по skill |
| **Fading — time to review** | Навыки, не практиковавшиеся >7 дней и percentage < 70%. Карточки с янтарным фоном |
| Skills overview | Без изменений (top 5 навыков) |
| Lessons list | Без изменений |

Функция `analyzeSkills()` классифицирует:
- `percentage === 0` → unstudied
- `percentage >= 70` → strong
- `percentage < 40` → weak
- `last_practiced_at > 7 дней` и `percentage < 70` → fading
- остальные → strong

### 3. Skills page (`pages/Skills.tsx`)

- Каждый навык помечен статус-бейджем: Strong 🟢 / Needs practice 🔴 / Fading 🟡 / Not studied ⚪
- Сортировка внутри категории: слабые → затухающие → сильные → неизученные
- Добавлена колонка **last practiced** (Today / Yesterday / N days ago / N months ago)
- В шапке страницы — счётчики strong/weak/fading с цветными точками
- Неизученные навыки отображаются полупрозрачными, без ссылки

### 4. Файлы

| Файл | Изменения |
|---|---|
| `frontend/src/types/index.ts` | `StudentSkill` + `last_practiced_at`, новый `SkillAnalysis` |
| `frontend/src/pages/Dashboard.tsx` | Полностью переписан: `analyzeSkills()`, блоки уровня/weak/fading |
| `frontend/src/pages/Skills.tsx` | `getSkillStatus()`, статус-бейджи, сортировка, last practiced |

### Проверка

- `npm run build` — 0 ошибок TypeScript, 0 ошибок сборки
- Все изменения только на фронтенде (бэкенд skills API не требует изменений)
