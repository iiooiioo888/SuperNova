"""健康检查 API"""
from fastapi import APIRouter
from sqlalchemy import text

from ..config import settings
from ..api.v1.deps import async_session_factory
from ..infrastructure.account_pool.service import account_pool_service
from ..infrastructure.circuit_breaker import circuit_breaker_manager

router = APIRouter(prefix="/health")


@router.get("/")
async def health_check():
    """基础健康检查"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check():
    """就绪检查 — 真实检测 PostgreSQL 和 Redis 连接"""
    checks = {}
    overall = "ready"

    # PostgreSQL
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgresql"] = "ok"
    except Exception as e:
        checks["postgresql"] = f"error: {e}"
        overall = "not_ready"

    # Redis
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        await client.close()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        overall = "not_ready"

    return {"status": overall, "checks": checks}


@router.get("/accounts/{platform}")
async def account_health(platform: str):
    """账号池健康检查"""
    return await account_pool_service.health_check(platform)


@router.get("/circuits")
async def circuit_status():
    """熔断器状态"""
    return {
        "circuits": circuit_breaker_manager.list_all(),
    }
