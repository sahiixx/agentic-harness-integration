"""Authentication and rate limiting for the API."""
from __future__ import annotations

import os
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

_JWT_SECRET: Optional[str] = None
_RATE_LIMIT: int = 60


def _get_jwt_secret() -> str:
    global _JWT_SECRET
    if _JWT_SECRET is None:
        _JWT_SECRET = os.getenv("JWT_SECRET", "")
    return _JWT_SECRET


def _get_rate_limit() -> int:
    global _RATE_LIMIT
    raw = os.getenv("RATE_LIMIT_PER_MINUTE", "60")
    try:
        _RATE_LIMIT = int(raw)
    except ValueError:
        _RATE_LIMIT = 60
    return _RATE_LIMIT


# In-memory rate limit store: {client_ip: [timestamp, ...]}
_rate_limit_store: dict[str, list[float]] = {}


def _clean_old_requests(timestamps: list[float], window: int = 60) -> list[float]:
    now = time.time()
    return [ts for ts in timestamps if now - ts < window]


def _is_rate_limited(client_ip: str) -> bool:
    limit = _get_rate_limit()
    if limit <= 0:
        return False

    now = time.time()
    _rate_limit_store[client_ip] = _clean_old_requests(_rate_limit_store.get(client_ip, []))
    _rate_limit_store[client_ip].append(now)
    return len(_rate_limit_store[client_ip]) > limit


async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """Verify JWT bearer token. Returns payload dict.

    If JWT_SECRET is not set, auth is disabled (returns empty dict).
    """
    secret = _get_jwt_secret()
    if not secret:
        return {}  # Auth disabled

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    import jwt
    try:
        payload = jwt.decode(credentials.credentials, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    if _is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )
    response = await call_next(request)
    return response


def create_token(subject: str, expires_minutes: int = 60) -> str:
    """Create a JWT token for a given subject."""
    import jwt
    secret = _get_jwt_secret()
    if not secret:
        raise RuntimeError("JWT_SECRET not set")
    now = time.time()
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + (expires_minutes * 60),
    }
    return jwt.encode(payload, secret, algorithm="HS256")
