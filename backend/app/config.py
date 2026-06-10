"""Application configuration via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Databases ---
    PLATFORM_DATABASE_URL: str = (
        "postgresql+asyncpg://user:password@localhost:5432/ai_mentor_platform"
    )
    TRAINING_DATABASE_URL: str = (
        "postgresql+asyncpg://user:password@localhost:5432/ai_mentor_training"
    )
    TRAINING_STATEMENT_TIMEOUT: int = 30

    # --- Lessons ---
    LESSONS_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "lessons")

    # --- JWT ---
    SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:4173"

    # --- Rate Limiting ---
    AUTH_RATE_LIMIT: str = "10/minute"
    GLOBAL_RATE_LIMIT: str = "100/minute"

    # --- GigaChat (Sberbank LLM) ---
    GIGACHAT_AUTH_KEY: str = ""
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"
    GIGACHAT_API_BASE: str = "https://gigachat.devices.sberbank.ru/api/v1"
    GIGACHAT_AUTH_URL: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    GIGACHAT_MODEL: str = "GigaChat"
    GIGACHAT_SSL_VERIFY: bool = False


settings = Settings()

if settings.SECRET_KEY in ("change-me", "change-me-to-a-random-secret-key"):
    import sys
    print(
        "FATAL: SECRET_KEY is set to a default insecure value!\n"
        "Generate a strong random key with: openssl rand -hex 32\n"
        "Then set it in your .env file as SECRET_KEY=<generated_key>",
        file=sys.stderr,
    )
    sys.exit(1)