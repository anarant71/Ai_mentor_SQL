"""Auth API: /api/v1/auth/* endpoints."""

import re
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import get_platform_session
from app.limiter import limiter
from app.middleware import require_active
from app.models.user import StudentProfile, User
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
    set_access_cookie,
    set_refresh_cookie,
    clear_auth_cookies,
    ACCESS_COOKIE,
    REFRESH_COOKIE,
)
from app.services.roadmap import create_default_roadmap

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def register(
    request: Request,
    body: UserCreate,
    response: Response,
    session: AsyncSession = Depends(get_platform_session),
):
    """Регистрация нового пользователя + создание student_profile."""
    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", body.email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "INVALID_EMAIL",
                "message": "Неверный формат email",
            },
        )
    
    # Validate password strength
    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "INVALID_PASSWORD",
                "message": "Пароль должен содержать не менее 6 символов",
            },
        )
    
    # Validate name field
    if not body.display_name or not body.display_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "INVALID_NAME",
                "message": "Имя пользователя обязательно",
            },
        )
    
    try:
        # Проверка: email уже занят
        existing = await session.execute(
            select(User).where(User.email == body.email)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMAIL_EXISTS",
                    "message": "Пользователь с таким email уже зарегистрирован",
                },
            )

        # Создание пользователя
        user = User(
            email=body.email.strip().lower(),
            password_hash=hash_password(body.password),
            display_name=body.display_name.strip(),
        )
        session.add(user)
        await session.flush()  # получаем user.id

        # Автоматическое создание student_profile
        profile = StudentProfile(user_id=user.id)
        session.add(profile)
        await session.commit()
        await session.refresh(user)

        # Создание roadmap (последовательность уроков)
        await create_default_roadmap(user.id, session)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        set_access_cookie(response, access_token)
        set_refresh_cookie(response, refresh_token)
        return UserRead.model_validate(user)
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "REGISTRATION_FAILED",
                "message": "Ошибка регистрации: пользователь уже существует или данные некорректны",
            },
        ) from e


@router.post("/login", response_model=UserRead)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def login(
    request: Request,
    body: UserLogin,
    response: Response,
    session: AsyncSession = Depends(get_platform_session),
):
    """Вход по email и паролю."""
    if not body.email or not body.email.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "MISSING_EMAIL",
                "message": "Email обязателен",
            },
        )

    if not body.password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "MISSING_PASSWORD",
                "message": "Пароль обязателен",
            },
        )

    result = await session.execute(
        select(User).where(User.email == body.email.strip().lower())
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Неверный email или пароль",
            },
        )

    if user.status == "blocked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "USER_BLOCKED",
                "message": "Пользователь заблокирован",
            },
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    set_access_cookie(response, access_token)
    set_refresh_cookie(response, refresh_token)
    return UserRead.model_validate(user)


@router.post("/refresh")
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    response: Response,
):
    """Обновить access_token через refresh_token cookie."""
    refresh_token_str = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_REFRESH_TOKEN",
                "message": "Refresh token не найден",
            },
        )

    user_id = decode_refresh_token(refresh_token_str)
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    set_access_cookie(response, access_token)
    set_refresh_cookie(response, refresh_token)
    return {"message": "Токены обновлены"}


@router.post("/logout")
@limiter.limit("20/minute")
async def logout(
    request: Request,
    response: Response,
):
    """Выход: очистить HttpOnly cookies."""
    clear_auth_cookies(response)
    return {"message": "Вы вышли из системы"}


@router.get("/me", response_model=UserRead)
@limiter.limit(settings.GLOBAL_RATE_LIMIT)
async def me(
    request: Request,
    current_user: User = Depends(require_active),
):
    """Данные текущего пользователя."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "Пользователь не найден",
            },
        )
    return UserRead.model_validate(current_user)