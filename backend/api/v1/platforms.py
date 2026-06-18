"""平台管理 API"""
from fastapi import APIRouter, HTTPException

from ..adapters.registry import list_adapters, get_adapter
from ..infrastructure.circuit_breaker import circuit_breaker_manager

router = APIRouter(prefix="/platforms")


@router.get("/")
async def list_platforms():
    """列出所有已接入的平台"""
    platforms = list_adapters()
    return {
        "platforms": platforms,
        "count": len(platforms),
    }


@router.get("/{platform}")
async def get_platform_info(platform: str):
    """获取平台详细信息"""
    try:
        adapter = get_adapter(platform)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    capabilities = adapter.capabilities()
    circuit_status = circuit_breaker_manager.get_status(platform)
    
    return {
        "platform": platform,
        "capabilities": [
            {
                "name": c.name,
                "description": c.description,
            }
            for c in capabilities
        ],
        "circuit_breaker": circuit_status,
    }
