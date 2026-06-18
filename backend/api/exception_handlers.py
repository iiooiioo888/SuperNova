"""全局异常处理器"""
from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.exceptions import (
    SuperHubError,
    AdapterError,
    AuthenticationError,
    RateLimitError,
    NoAvailableAccountError,
    CircuitOpenError,
    SkipTask,
    FeatureDisabledError,
)
from backend.adapters.exceptions import CapabilityNotSupported, UnknownPlatformError

logger = structlog.get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        logger.warning("auth.error", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=401,
            content={"error": "authentication_failed", "detail": str(exc)},
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError):
        logger.warning("rate_limit.error", path=request.url.path, retry_after=exc.retry_after)
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limit_exceeded", "detail": str(exc)},
            headers=headers,
        )

    @app.exception_handler(NoAvailableAccountError)
    async def no_account_handler(request: Request, exc: NoAvailableAccountError):
        logger.warning("account.none_available", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=503,
            content={"error": "no_available_account", "detail": str(exc)},
        )

    @app.exception_handler(CircuitOpenError)
    async def circuit_open_handler(request: Request, exc: CircuitOpenError):
        logger.warning("circuit.open", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=503,
            content={"error": "circuit_breaker_open", "detail": str(exc)},
        )

    @app.exception_handler(CapabilityNotSupported)
    async def capability_handler(request: Request, exc: CapabilityNotSupported):
        return JSONResponse(
            status_code=400,
            content={
                "error": "capability_not_supported",
                "detail": str(exc),
                "capability": exc.capability_name,
                "platform": exc.platform,
            },
        )

    @app.exception_handler(UnknownPlatformError)
    async def unknown_platform_handler(request: Request, exc: UnknownPlatformError):
        return JSONResponse(
            status_code=404,
            content={"error": "unknown_platform", "detail": str(exc)},
        )

    @app.exception_handler(FeatureDisabledError)
    async def feature_disabled_handler(request: Request, exc: FeatureDisabledError):
        logger.info("feature.disabled", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=403,
            content={"error": "feature_disabled", "detail": str(exc)},
        )

    @app.exception_handler(SkipTask)
    async def skip_task_handler(request: Request, exc: SkipTask):
        logger.info("task.skipped", path=request.url.path, reason=str(exc))
        return JSONResponse(
            status_code=200,
            content={"status": "skipped", "reason": str(exc)},
        )

    @app.exception_handler(AdapterError)
    async def adapter_error_handler(request: Request, exc: AdapterError):
        logger.error("adapter.error", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=502,
            content={"error": "adapter_error", "detail": str(exc)},
        )

    @app.exception_handler(SuperHubError)
    async def base_error_handler(request: Request, exc: SuperHubError):
        logger.error("app.error", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("app.unhandled_error", path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "detail": "An unexpected error occurred"},
        )
