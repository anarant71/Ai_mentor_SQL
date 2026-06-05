"""Auth API: /api/v1/auth/* endpoints."""

import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database import get_platform_session
from app.middleware import require_active
from app.models.user import StudentProfile, User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserRead
from app.services.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: UserCreate,
    session: AsyncSession = Depends(get_platform_session),
):
    """Регистрация нового пользователя + создание student_profile."""
    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", body.email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_EMAIL",
                "message": "Неверный формат email",
            },
        )
    
    # Validate password strength
    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_PASSWORD",
                "message": "Пароль должен содержать не менее 6 символов",
            },
        )
    
    # Validate name field
    if not body.display_name or not body.display_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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

        token = create_access_token(user.id)
        return TokenResponse(
            access_token=token,
            user=UserRead.model_validate(user),
        )
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "REGISTRATION_FAILED",
                "message": "Ошибка регистрации: пользователь уже существует или данные некорректны",
            },
        ) from e


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLogin,
    session: AsyncSession = Depends(get_platform_session),
):
    """Вход по email и паролю."""
    try:
        # Validate input
        if not body.email or not body.email.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "MISSING_EMAIL",
                    "message": "Email обязателен",
                },
            )
        
        if not body.password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
                status = status.HTTP_401_UNAUTHORIZED,
                detail = {
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

        token = create_access_token(user.id)
        return TokenResponse(
            access_token=token,
            user=UserRead.model_validate(user),
        )


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(require_active)):
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