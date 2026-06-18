"""限流器实现"""
from __future__ import annotations

import time
import asyncio
from collections import defaultdict
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class TokenBucketRateLimiter:
    """令牌桶限流器
    
    每个平台独立限流，支持动态调整速率。
    """

    def __init__(
        self,
        rate: float = 10.0,  # 每秒产生的令牌数
        capacity: int = 20,  # 桶容量
    ):
        self._rate = rate
        self._capacity = capacity
        self._buckets: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"tokens": capacity, "last_refill": time.monotonic()}
        )
        self._lock = asyncio.Lock()

    async def acquire(self, key: str = "default", tokens: int = 1) -> bool:
        """尝试获取令牌
        
        Args:
            key: 限流键（通常为平台名）
            tokens: 需要的令牌数
            
        Returns:
            bool: True 表示获取成功，False 表示被限流
        """
        async with self._lock:
            bucket = self._buckets[key]
            now = time.monotonic()

            # 补充令牌
            elapsed = now - bucket["last_refill"]
            bucket["tokens"] = min(
                self._capacity,
                bucket["tokens"] + elapsed * self._rate,
            )
            bucket["last_refill"] = now

            if bucket["tokens"] >= tokens:
                bucket["tokens"] -= tokens
                return True

            logger.warning("rate_limiter.blocked", key=key, tokens_requested=tokens)
            return False

    async def wait_and_acquire(
        self, key: str = "default", tokens: int = 1, timeout: float = 30.0
    ) -> bool:
        """等待并获取令牌
        
        阻塞直到获取成功或超时。
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if await self.acquire(key, tokens):
                return True
            # 计算需要等待的时间
            async with self._lock:
                bucket = self._buckets[key]
                wait_time = max(
                    0.01,
                    (tokens - bucket["tokens"]) / self._rate,
                )
            await asyncio.sleep(min(wait_time, 1.0))
        return False

    def get_status(self, key: str = "default") -> dict[str, Any]:
        """获取指定键的限流状态"""
        bucket = self._buckets.get(key)
        if not bucket:
            return {"key": key, "tokens": self._capacity, "rate": self._rate}
        return {
            "key": key,
            "tokens": round(bucket["tokens"], 2),
            "capacity": self._capacity,
            "rate": self._rate,
        }

    def update_rate(self, rate: float) -> None:
        """动态调整速率"""
        self._rate = rate
        logger.info("rate_limiter.rate_updated", rate=rate)


# 全局单例
rate_limiter = TokenBucketRateLimiter()
