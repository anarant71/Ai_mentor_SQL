"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.auth import router as auth_router
from app.api.lessons import router as lessons_router
from app.api.tasks import router as tasks_router
from app.api.sandbox import router as sandbox_router
from app.api.skills import router as skills_router
from app.api.mistakes import router as mistakes_router
from app.api.mentor import router as mentor_router
from app.config import settings
from app.database import (
    check_platform_db,
    check_training_db,
    close_databases,
    init_databases,
)
from app.limiter import limiter
from app.models.base import Base
from app.database import platform_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_databases()
    # Auto-create any tables missing from migrations (e.g. roadmaps)
    async with platform_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await close_databases()


app = FastAPI(
    title="AI-Mentor Platform API",
    description="Backend for the AI-Mentor SQL learning platform. MVP 0.1.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    headers = getattr(exc, "headers", None)
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        body = {"error": detail}
    else:
        body = {"error": {"code": "HTTP_ERROR", "message": str(detail)}}
    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        headers=headers,
    )


app.include_router(auth_router)
app.include_router(lessons_router)
app.include_router(tasks_router)
app.include_router(sandbox_router)
app.include_router(skills_router)
app.include_router(mistakes_router)
app.include_router(mentor_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else [],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(SlowAPIMiddleware)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "ai-mentor-api", "version": "0.1.0"}


@app.get("/health/db", tags=["health"])
async def health_db():
    platform_status = await check_platform_db()
    training_status = await check_training_db()
    all_ok = (
        platform_status["status"] == "ok"
        and training_status["status"] == "ok"
    )
    return {
        "status": "ok" if all_ok else "degraded",
        "platform_db": platform_status,
        "training_db": training_status,
    }