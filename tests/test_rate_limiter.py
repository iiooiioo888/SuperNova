"""限流器测试"""
import pytest
import asyncio
from backend.infrastructure.rate_limiter import TokenBucketRateLimiter


@pytest.mark.asyncio
async def test_acquire_within_capacity():
    """桶内有令牌时应成功"""
    limiter = TokenBucketRateLimiter(rate=10, capacity=5)
    assert await limiter.acquire("test") is True


@pytest.mark.asyncio
async def test_acquire_exhausted():
    """令牌耗尽后应被限流"""
    limiter = TokenBucketRateLimiter(rate=0.01, capacity=2)
    assert await limiter.acquire("test") is True
    assert await limiter.acquire("test") is True
    assert await limiter.acquire("test") is False


@pytest.mark.asyncio
async def test_separate_keys():
    """不同 key 互相独立"""
    limiter = TokenBucketRateLimiter(rate=0.01, capacity=1)
    assert await limiter.acquire("a") is True
    assert await limiter.acquire("b") is True
    assert await limiter.acquire("a") is False


def test_get_status():
    """状态查询"""
    limiter = TokenBucketRateLimiter(rate=10, capacity=20)
    status = limiter.get_status("test")
    assert status["capacity"] == 20
    assert status["rate"] == 10


def test_update_rate():
    """动态调整速率"""
    limiter = TokenBucketRateLimiter(rate=10, capacity=20)
    limiter.update_rate(50)
    assert limiter._rate == 50
