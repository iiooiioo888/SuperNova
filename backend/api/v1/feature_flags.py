"""功能開關管理 API"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Any
from datetime import datetime
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.deps import get_redis, get_db_session, get_current_user
from backend.services.feature_flag import (
    FeatureFlagService,
    FlagScope,
    FeatureFlagCreate,
    FeatureFlagUpdate,
    get_feature_flag_service,
)
from backend.models.pg.auth import User  # 假設有用戶模型

router = APIRouter(prefix="/feature-flags", tags=["Feature Flags"])


@router.get("/list")
async def list_feature_flags(
    scope: FlagScope | None = Query(None, description="篩選作用域"),
    platform: str | None = Query(None, description="篩選平台"),
    enabled_only: bool = Query(False, description="僅顯示啟用的開關"),
    service: FeatureFlagService = Depends(get_feature_flag_service),
) -> dict[str, Any]:
    """列出所有功能開關"""
    flags = await service.list_flags(
        scope=scope,
        platform=platform,
        enabled_only=enabled_only,
    )
    return {"count": len(flags), "items": flags}


@router.get("/{name}")
async def get_feature_flag(
    name: str,
    platform: str | None = Query(None, description="平台标识"),
    service: FeatureFlagService = Depends(get_feature_flag_service),
) -> dict[str, Any]:
    """獲取指定開關詳情"""
    flag = await service.get_flag(name, platform)
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return flag


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    payload: FeatureFlagCreate,
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service),
) -> dict[str, Any]:
    """創建新的功能開關
    
    權限要求：role='admin' or role='ops'
    """
    # 權限檢查（實際應通過 middleware 或 decorator 實現）
    if current_user.role not in ["admin", "ops"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Requires 'admin' or 'ops' role.",
        )
    
    model = await service.set_flag(
        name=payload.name,
        enabled=payload.enabled,
        scope=payload.scope,
        platform=payload.platform,
        reason="Created via API",
        changed_by=current_user.username,
        metadata=payload.metadata,
        restore_at=payload.restore_at,
        gray_scale=payload.gray_scale,
    )
    
    return {
        "id": model.id,
        "name": model.name,
        "scope": model.scope,
        "platform": model.platform,
        "enabled": model.enabled,
    }


@router.patch("/{name}")
async def update_feature_flag(
    name: str,
    payload: FeatureFlagUpdate,
    platform: str | None = Query(None, description="平台标识"),
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service),
) -> dict[str, Any]:
    """更新功能開關狀態
    
    權限要求：role='admin' or role='ops'
    審計記錄：自動記錄變更原因和操作者
    """
    if current_user.role not in ["admin", "ops"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Requires 'admin' or 'ops' role.",
        )
    
    # 確定作用域
    scope = FlagScope.PLATFORM if platform else FlagScope.STRATEGY
    
    model = await service.set_flag(
        name=name,
        enabled=payload.enabled if payload.enabled is not None else True,
        scope=scope,
        platform=platform,
        reason=payload.reason,
        changed_by=current_user.username,
        metadata=payload.metadata,
        restore_at=payload.restore_at,
        gray_scale=payload.gray_scale,
    )
    
    return {
        "id": model.id,
        "enabled": model.enabled,
        "gray_scale": model.gray_scale,
        "restore_at": model.restore_at.isoformat() if model.restore_at else None,
        "updated_at": model.updated_at.isoformat(),
    }


@router.post("/platforms/{platform}/disable")
async def disable_platform(
    platform: str,
    reason: str = Query(..., description="禁用原因"),
    auto_restore_minutes: int | None = Query(None, description="自動恢復時間（分鐘）"),
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service),
) -> dict[str, Any]:
    """緊急禁用整個平台
    
    使用場景：熔斷器觸發、API 大面積失敗、運維手動降級
    權限要求：role='admin' or role='ops'
    """
    if current_user.role not in ["admin", "ops"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Requires 'admin' or 'ops' role.",
        )
    
    await service.disable_platform(
        platform=platform,
        reason=reason,
        changed_by=current_user.username,
        auto_restore_minutes=auto_restore_minutes,
    )
    
    return {
        "status": "success",
        "platform": platform,
        "action": "disabled",
        "reason": reason,
        "auto_restore_minutes": auto_restore_minutes,
    }


@router.post("/platforms/{platform}/enable")
async def enable_platform(
    platform: str,
    reason: str = Query(..., description="啟用原因"),
    current_user: User = Depends(get_current_user),
    service: FeatureFlagService = Depends(get_feature_flag_service),
) -> dict[str, Any]:
    """啟用平台"""
    if current_user.role not in ["admin", "ops"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Requires 'admin' or 'ops' role.",
        )
    
    await service.enable_platform(
        platform=platform,
        reason=reason,
        changed_by=current_user.username,
    )
    
    return {
        "status": "success",
        "platform": platform,
        "action": "enabled",
        "reason": reason,
    }


@router.get("/scheduled-restores")
async def get_scheduled_restores(
    service: FeatureFlagService = Depends(get_feature_flag_service),
) -> dict[str, Any]:
    """獲取待恢復的平台列表"""
    restores = await service.get_scheduled_restores()
    return {"count": len(restores), "items": restores}


@router.get("/check/{name}")
async def check_feature_flag(
    name: str,
    platform: str | None = Query(None, description="平台标识"),
    user_id: str | None = Query(None, description="用戶 ID（用於灰度判斷）"),
    service: FeatureFlagService = Depends(get_feature_flag_service),
) -> dict[str, bool]:
    """檢查開關是否對當前請求啟用
    
    支持灰度發布邏輯判斷
    """
    enabled = await service.is_enabled(name, platform, user_id)
    return {"enabled": enabled}
