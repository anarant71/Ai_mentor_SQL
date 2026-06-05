"""Auth services: хэширование, JWT, получение текущего пользователя."""

from uuid import UUID

from fastapi import Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_platform_session
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _set_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    """Установить HttpOnly cookie."""
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=False,  # True в production через HTTPS
        samesite="lax",
        max_age=max_age,
        path="/",
    )


def _delete_cookie(response: Response, key: str) -> None:
    """Очистить HttpOnly cookie."""
    response.delete_cookie(key, path="/")


def set_access_cookie(response: Response, token: str) -> None:
    """Установить access_token cookie (15 min)."""
    _set_cookie(
        response, ACCESS_COOKIE, token,
        settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )


def set_refresh_cookie(response: Response, token: str) -> None:
    """Установить refresh_token cookie (7 days)."""
    _set_cookie(
        response, REFRESH_COOKIE, token,
        settings.JWT_REFRESH_EXPIRE_DAYS * 86400,
    )


def clear_auth_cookies(response: Response) -> None:
    """Очистить все auth-куки."""
    _delete_cookie(response, ACCESS_COOKIE)
    _delete_cookie(response, REFRESH_COOKIE)


def hash_password(password: str) -> str:
    """Вернуть bcrypt-хэш пароля."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить пароль против хэша."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: UUID) -> str:
    """Создать JWT access token (15 min)."""
    from datetime import datetime, timedelta, timezone

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(user_id: UUID) -> str:
    """Создать JWT refresh token (7 days)."""
    from datetime import datetime, timedelta, timezone

    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_EXPIRE_DAYS
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def _decode_token(token: str, expected_type: str | None = None) -> UUID:
    """Декодировать JWT, опционально проверить тип."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Невалидный токен"},
            )
        if expected_type and payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "WRONG_TOKEN_TYPE", "message": "Неверный тип токена"},
            )
        return UUID(user_id_str)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Невалидный токен"},
        )


def decode_access_token(token: str) -> UUID:
    """Декодировать access token."""
    return _decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> UUID:
    """Декодировать refresh token."""
    return _decode_token(token, expected_type="refresh")
    """Декодировать JWT и вернуть UUID пользователя."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Невалидный токен"},
            )
        return UUID(user_id_str)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Невалидный токен"},
        )


def _extract_token(request: Request) -> str | None:
    """Извлечь JWT из Authorization header или HttpOnly cookie."""
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:]
    return request.cookies.get(ACCESS_COOKIE)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_platform_session),
) -> User:
    """FastAPI dependency: извлечь и проверить токен, вернуть User."""
    token = _extract_token(request)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_TOKEN",
                "message": "Токен авторизации не предоставлен",
            },
        )

    user_id = decode_access_token(token)
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "Пользователь не найден",
            },
        )
    return user