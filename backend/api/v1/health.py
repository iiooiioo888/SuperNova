"""健康检查 API"""
from fastapi import APIRouter

from ..config import settings
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
    """就绪检查"""
    return {
        "status": "ready",
    }


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
