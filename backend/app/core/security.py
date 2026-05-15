from uuid import UUID

from fastapi import Cookie, Header, HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


def get_current_user_id(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
) -> UUID:
    token = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
            )
        return UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
