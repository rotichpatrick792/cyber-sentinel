"""Authentication endpoints: /register and /login.

Registration creates a User row. Login verifies credentials and returns
a JWT the client must send as `Authorization: Bearer <token>` on
protected requests.

Both endpoints are rate-limited per client IP to deter brute-force attacks.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.models.schemas import Token, UserCreate, UserLogin, UserPublic
from app.models.user import User

logger = get_logger(__name__)

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=201)
@limiter.limit("3/minute")
async def register(
    request: Request,
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    # Check for existing username or email.
    existing = db.scalar(
        select(User).where(
            or_(User.username == payload.username, User.email == payload.email)
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Registered user id=%s username=%s", user.id, user.username)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    payload: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    token = create_access_token(subject=user.id)
    logger.info("Login success user id=%s", user.id)
    return Token(access_token=token)
