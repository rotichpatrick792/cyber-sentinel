"""Shared FastAPI dependencies.

`get_current_user` is the standard "requires login" dependency used by
any endpoint that should only be reachable with a valid JWT.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# HTTPBearer gives Swagger UI a simple "paste your token" field
# instead of an OAuth2 username/password form.
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Return the logged-in User, or raise 401."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exc

    sub = decode_access_token(credentials.credentials)
    if sub is None:
        raise credentials_exc

    try:
        user_id = int(sub)
    except ValueError:
        raise credentials_exc

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise credentials_exc
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    return user
