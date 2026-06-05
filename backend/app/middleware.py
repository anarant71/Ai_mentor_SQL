"""Auth middleware: зависимости для защиты маршрутов.

- get_current_user: проверить Bearer token, вернуть User (из services/auth)
- require_active: проверить, что пользователь активен
- require_admin: проверить, что пользователь admin
"""

from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.services.auth import get_current_user


async def require_active(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверить, что пользователь активен (не заблокирован)."""
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "USER_BLOCKED",
                "message": "Пользователь заблокирован",
            },
        )
    return current_user


async def require_admin(
    current_user: User = Depends(require_active),
) -> User:
    """Проверить, что пользователь имеет роль admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Доступ запрещён. Требуется роль администратора",
            },
        )
    return current_user