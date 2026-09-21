from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError
from app.core.security import decode_token
from app.models import User

bearer = HTTPBearer(auto_error=False)


async def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise AppError("未登录", 401, 401)
    try:
        user = await db.get(User, decode_token(credentials.credentials))
    except Exception:
        raise AppError("登录已过期", 401, 401) from None
    if not user:
        raise AppError("用户不存在", 401, 401)
    return user


async def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise AppError("无管理员权限", 403, 403)
    return user
