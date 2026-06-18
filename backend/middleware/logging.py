"""请求日志与追踪中间件"""
from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件

    为每个请求生成唯一 request_id，记录耗时和状态码。
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.monotonic()
        logger.info(
            "request.start",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params),
            client=request.client.host if request.client else None,
        )

        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request.error", path=request.url.path)
            raise
        finally:
            elapsed = round((time.monotonic() - start) * 1000, 1)
            logger.info(
                "request.end",
                method=request.method,
                path=request.url.path,
                status=response.status_code if "response" in dir() else 500,
                elapsed_ms=elapsed,
            )
            structlog.contextvars.unbind_contextvars("request_id")

        response.headers["X-Request-ID"] = request_id
        return response
