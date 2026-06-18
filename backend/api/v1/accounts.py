"""账号池 API"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Any

from ..infrastructure.account_pool.service import account_pool_service, AccountLease

router = APIRouter(prefix="/accounts")


class AddAccountRequest(BaseModel):
    platform: str
    account_id: str
    credentials: dict[str, Any]


@router.post("/add")
async def add_account(request: AddAccountRequest):
    """添加账号到池中"""
    await account_pool_service.add_account(
        platform=request.platform,
        account_id=request.account_id,
        credentials=request.credentials,
    )
    return {"status": "ok", "account_id": request.account_id}


@router.get("/{platform}/health")
async def account_health(platform: str):
    """获取账号池健康状态"""
    return await account_pool_service.health_check(platform)


@router.post("/{platform}/acquire")
async def acquire_account(platform: str, task_type: str = Body(default="default")):
    """获取账号租约"""
    try:
        lease = await account_pool_service.acquire(platform, task_type)
        return {
            "lease_id": lease.lease_id,
            "platform": lease.platform,
            "account_id": lease.account_id,
            "expires_at": lease.expires_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{platform}/release")
async def release_account(platform: str, lease_id: str = Body(...)):
    """释放账号租约"""
    # TODO: 需要根据 lease_id 找到对应的租约
    return {"status": "ok"}
