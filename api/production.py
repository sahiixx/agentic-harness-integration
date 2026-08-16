"""Production hardening: logging, rate limiting, circuit breakers, tracing."""
from __future__ import annotations

import os
import time
import uuid
import logging
from contextvars import ContextVar
from typing import Any, Callable, Dict, Optional

import structlog
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

# ─── Structured Logging ───
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# ─── Request ID Tracing ───
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_var.get() or "no-request-id"


def set_request_id(req_id: str) -> None:
    request_id_var.set(req_id)


class RequestIDMiddleware:
    """Add request ID to all log entries."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers_dict = dict(scope.get("headers", []))
        req_id = headers_dict.get(b"x-request-id", b"").decode() or str(uuid.uuid4())[:8]
        set_request_id(req_id)

        structlog.contextvars.bind_contextvars(request_id=req_id)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", req_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            structlog.contextvars.clear_contextvars()


# ─── Circuit Breaker ───
class CircuitBreaker:
    """Wrapper for circuitbreaker with configurable defaults."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

    def __call__(self, func: Callable) -> Callable:
        @circuit(
            failure_threshold=self.failure_threshold,
            recovery_timeout=self.recovery_timeout,
            expected_exception=self.expected_exception,
        )
        @retry(
            wait=wait_exponential_jitter(initial=0.1, max=2.0),
            stop=stop_after_attempt(3),
        )
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper


# ─── Redis Rate Limiter ───
class RedisRateLimiter:
    """Distributed rate limiter using Redis (redis-py async)."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        cost: int = 1,
    ) -> tuple[bool, dict]:
        """
        Check rate limit using sliding window.
        Returns (allowed, metadata).
        """
        client = await self._get_client()
        now = time.time()
        window_start = now - window

        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window + 1)
        results = await pipe.execute()

        current_count = results[1]
        allowed = current_count < limit

        return allowed, {
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "reset": int(now + window),
            "retry_after": 0 if allowed else window,
        }

    async def close(self):
        if self._client:
            await self._client.close()


# ─── Retry Policies ───
RETRY_POLICIES = {
    "default": retry(
        wait=wait_exponential_jitter(initial=0.5, max=4.0),
        stop=stop_after_attempt(3),
    ),
    "aggressive": retry(
        wait=wait_exponential_jitter(initial=0.1, max=1.0),
        stop=stop_after_attempt(5),
    ),
    "conservative": retry(
        wait=wait_exponential_jitter(initial=1.0, max=10.0),
        stop=stop_after_attempt(2),
    ),
}


def with_retry(policy: str = "default"):
    """Decorator for retry policies."""
    return RETRY_POLICIES.get(policy, RETRY_POLICIES["default"])


# ─── Health Check Registry ───
class HealthRegistry:
    """Centralized health check registry."""

    def __init__(self):
        self._checks: Dict[str, Callable] = {}

    def register(self, name: str, check_fn: Callable) -> None:
        self._checks[name] = check_fn

    async def run_all(self) -> Dict[str, Any]:
        results = {}
        for name, check_fn in self._checks.items():
            start = time.time()
            try:
                result = await check_fn()
                results[name] = {
                    "status": "healthy" if result.get("healthy", True) else "unhealthy",
                    "latency_ms": int((time.time() - start) * 1000),
                    "details": result,
                }
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "latency_ms": int((time.time() - start) * 1000),
                    "error": str(e),
                }
        return results


health_registry = HealthRegistry()


# ─── Error Response Standardization ───
class ErrorResponse:
    """Standardized error responses."""

    @staticmethod
    def validation_error(detail: str, field: str = "") -> dict:
        return {
            "error": "validation_error",
            "message": detail,
            "field": field,
            "request_id": get_request_id(),
        }

    @staticmethod
    def rate_limit_exceeded(retry_after: int) -> dict:
        return {
            "error": "rate_limit_exceeded",
            "message": "Rate limit exceeded",
            "retry_after": retry_after,
            "request_id": get_request_id(),
        }

    @staticmethod
    def circuit_open(service: str) -> dict:
        return {
            "error": "circuit_open",
            "message": f"Service {service} temporarily unavailable",
            "request_id": get_request_id(),
        }

    @staticmethod
    def internal_error(detail: str = "Internal server error") -> dict:
        return {
            "error": "internal_error",
            "message": detail,
            "request_id": get_request_id(),
        }

    @staticmethod
    def not_found(resource: str) -> dict:
        return {
            "error": "not_found",
            "message": f"{resource} not found",
            "request_id": get_request_id(),
        }

    @staticmethod
    def unauthorized() -> dict:
        return {
            "error": "unauthorized",
            "message": "Authentication required",
            "request_id": get_request_id(),
        }


# ─── Configuration ───
class ProductionConfig:
    """Production configuration with defaults."""

    # Rate limiting
    RATE_LIMIT_DEFAULT = 100  # requests per window
    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_AUTH = 10  # stricter for auth endpoints

    # Circuit breaker
    CB_FAILURE_THRESHOLD = 5
    CB_RECOVERY_TIMEOUT = 30

    # Timeouts
    HTTP_TIMEOUT = 30.0
    OLLAMA_TIMEOUT = 60.0
    GROK_TIMEOUT = 60.0

    # Retry
    MAX_RETRIES = 3
    BASE_DELAY = 0.5

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Circuit breaker
    CB_ENABLED = os.getenv("CB_ENABLED", "true").lower() == "true"


config = ProductionConfig()