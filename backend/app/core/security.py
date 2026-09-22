"""Password hashing.

JWT helpers arrive in Step 3. For now we only need hashing.
"""

from __future__ import annotations

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings

# bcrypt is the industry default for password hashing. The "deprecated=auto"
# setting allows future algorithm migrations without breaking existing hashes.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the given password."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Check whether a plaintext password matches a stored hash."""
    return pwd_context.verify(plain, hashed)

_settings = get_settings()


def create_access_token(subject: str | int, expires_minutes: int | None = None) -> str:
    """Return a signed JWT with `sub` set to the subject (usually user id)."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or _settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, _settings.secret_key, algorithm=_settings.algorithm)


def decode_access_token(token: str) -> str | None:
    """Return the `sub` claim from a valid token, or None if invalid/expired."""
    try:
        payload = jwt.decode(
            token, _settings.secret_key, algorithms=[_settings.algorithm]
        )
        return payload.get("sub")
    except JWTError:
        return None
