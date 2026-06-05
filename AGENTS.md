# AI Mentor — Session Handoff

## Summary
Full refactor: HttpOnly cookies + rate limiting + React Query + sequential lesson roadmap + test infrastructure.

## Changes

### Security
- **JWT moved from localStorage to HttpOnly cookies**: `access_token` (15min) + `refresh_token` (7 days) via `Set-Cookie`
- **Rate limiting via slowapi**: `/auth/register` and `/auth/login` 10/min, `/auth/logout` and `/auth/refresh` 20/min, `/auth/me` 100/min
- **CORS**: `withCredentials: true` on frontend client

### Auth
- **Refresh token flow**: `POST /auth/refresh` reads `refresh_token` cookie, issues new pair; 401 interceptor in `api/client.ts` retries once before redirecting to `/login`
- **Bugfix**: `HTTPException(status=...)` → `status_code=` in `/auth/login` (line 153)
- **Deprecation cleanup**: `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT` (5 occurrences)
- `AuthContext` init calls `/auth/me` (cookie sent automatically); login/register returns `User` directly; logout calls `POST /auth/logout`

### Sequential Learning (Roadmap)
- **`create_default_roadmap()` now called on registration** (`backend/app/api/auth.py:104`)
- **`GET /api/v1/lessons`** returns `roadmap_status` per lesson (`locked`/`available`/`completed`)
- **`GET /api/v1/lessons/{slug}`** returns `roadmap_status`
- **`POST /.../progress`**: blocks `completed` for locked lessons (`403 LESSON_LOCKED`); calls `advance_roadmap_step()` on completion to unlock next
- **Frontend**: Dashboard shows locked lessons greyed out (🔒, not clickable); LessonPage shows "locked" screen when `roadmap_status === 'locked'`
- `LessonListItem` and `LessonDetail` schemas include `roadmap_status`

### SQL Sandbox
- AST parsing via `sqlparse` already implemented in `services/sandbox.py` — no changes needed

### Frontend — React Query
- `@tanstack/react-query` installed, `QueryClientProvider` in `App.tsx` (30s staleTime)
- All pages refactored from `useEffect`+`useState` → `useQuery`/`useMutation`:
  - `Dashboard.tsx` — `useQuery` for lessons + skills
  - `Skills.tsx` — `useQuery` for skills
  - `Mistakes.tsx` — `useQuery` + `useMutation` with `invalidateQueries`
  - `TaskBook.tsx` — `useQuery` for skills + tasks
  - `Lesson.tsx` — `useQuery` for lesson + tasks + allLessons; `useMutation` for submit

### New Pages
- `/mistakes` — status filter pills, "Resolve all" button, `StudentMistake`/`MistakeType` types

### Test Infrastructure
- `conftest.py` rewritten: sync SQLAlchemy fixtures for DB cleanup (event-loop-agnostic); `Base.metadata.create_all` at session start; `DELETE FROM all tables` between tests
- Auth tests converted to sync with `TestClient` fixture (was module-level `client`), 8/8 pass
- PostgreSQL databases created in Docker (`mentor_app` user, `ai_mentor_platform` + `ai_mentor_training`)

## Key Files

### Backend
| File | Purpose |
|---|---|
| `app/services/auth.py` | Cookie helpers (`set_access_cookie`, `set_refresh_cookie`, `clear_auth_cookies`), `_extract_token`, `_decode_token`, `create_access_token` (15min), `create_refresh_token` (7d) |
| `app/api/auth.py` | Auth endpoints with `@limiter.limit`, roadmap creation on register |
| `app/api/lessons.py` | Lesson endpoints with roadmap checks |
| `app/services/lessons.py` | `get_lessons_with_progress` includes `roadmap_status`; `upsert_progress` blocks locked |
| `app/services/roadmap.py` | `create_default_roadmap`, `advance_roadmap_step` |
| `app/schemas/lesson.py` | `LessonListItem`, `LessonDetail` with `roadmap_status` |
| `app/limiter.py` | Shared `Limiter` instance |
| `app/config.py` | Rate limit settings + JWT expiry config |
| `app/main.py` | `SlowAPIMiddleware`, limiter state, `RateLimitExceeded` handler |
| `tests/conftest.py` | Sync DB cleanup fixtures |
| `tests/test_auth.py` | 8 auth tests |

### Frontend
| File | Purpose |
|---|---|
| `src/api/client.ts` | Axios with `withCredentials`, 401 interceptor with refresh |
| `src/context/AuthContext.tsx` | No localStorage, `/auth/me` init, logout calls API |
| `src/App.tsx` | `QueryClientProvider`, `/mistakes` route |
| `src/pages/Dashboard.tsx` | Locked lesson rendering (greyed + 🔒) |
| `src/pages/Lesson.tsx` | Locked screen, React Query refactor |
| `src/pages/Mistakes.tsx` | Status filters, resolve mutation |
| `src/types/index.ts` | `Lesson` with `roadmap_status`, `StudentMistake`, `MistakeType` |

## Known Issues / Dead Code
- `SECRET_KEY = "change-me"` in `app/config.py` causes `sys.exit(1)` at startup if `.env` not set
- `TokenResponse` in `app/schemas/user.py` is unused (no imports)
- `AuthResponse` type in `frontend/src/types/index.ts` is unused (removed from imports but type definition still exists)
- `frontend/src/components/ProtectedRoute.tsx` checks auth only — no lesson-level access (delegated to backend + Lesson page)
- The refresh interceptor in `api/client.ts` retries the original request once after a successful refresh; if refresh also fails (401), user is redirected to `/login`

## Running Tests
```bash
# Backend (needs PostgreSQL running on localhost:5432)
cd backend && PYTHONPATH=. python3 -m pytest -v

# Frontend
cd frontend && npm run build
```
