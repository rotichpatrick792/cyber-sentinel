"""Password hashing.

JWT helpers arrive in Step 3. For now we only need hashing.
"""

from __future__ import annotations

from passlib.context import CryptContext

# bcrypt is the industry default for password hashing. The "deprecated=auto"
# setting allows future algorithm migrations without breaking existing hashes.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the given password."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Check whether a plaintext password matches a stored hash."""
    return pwd_context.verify(plain, hashed)
