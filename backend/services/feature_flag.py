"""功能開關與模塊控制服務"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timedelta
from typing import Any
from enum import Enum
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.models.pg.feature_flag import FeatureFlagModel, FeatureFlagAuditLog
from backend.exceptions import SuperHubError

logger = structlog.get_logger(__name__)


class FlagScope(str, Enum):
    """開關作用域"""
    GLOBAL = "global"
    PLATFORM = "platform"
    FEATURE = "feature"
    STRATEGY = "strategy"


class FeatureFlagCreate(BaseModel):
    """創建開關請求"""
    name: str
    scope: FlagScope
    enabled: bool = True
    platform: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    restore_at: datetime | None = None
    gray_scale: float = 1.0  # 灰度比例 0.0-1.0
    target_users: list[str] = Field(default_factory=list)


class FeatureFlagUpdate(BaseModel):
    """更新開關請求"""
    enabled: bool | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None
    restore_at: datetime | None = None
    gray_scale: float | None = None
    target_users: list[str] | None = None
    reason: str | None = None  # 變更原因（審計用）


class FeatureFlagService:
    """功能開關服務
    
    四層控制架構：
    1. Global: 全局開關（緊急制動）
    2. Platform: 平台級開關（bilibili, douyin, ...）
    3. Feature: 功能級開關（posts, live, comments, search）
    4. Strategy: 策略級開關（new_parser, aggressive_mode, ...）
    
    存儲策略：
    - Redis: 高性能讀取（TTL 5 分鐘）
    - PostgreSQL: 持久化 + 審計日誌
    """
    
    REDIS_PREFIX = "superhub:flags"
    REDIS_TTL = 300  # 5 分鐘
    
    def __init__(self, redis: Redis, db_session: AsyncSession):
        self._redis = redis
        self._db = db_session
    
    async def get_flag(self, name: str, platform: str | None = None) -> dict[str, Any]:
        """獲取開關狀態
        
        優先從 Redis 緩存讀取，未命中則查 DB 並回寫緩存
        """
        cache_key = self._build_cache_key(name, platform)
        
        # 嘗試從 Redis 讀取
        cached = await self._redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 從 DB 查詢
        query = select(FeatureFlagModel).where(FeatureFlagModel.name == name)
        if platform:
            query = query.where(FeatureFlagModel.platform == platform)
        
        result = await self._db.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            # 默認開啟
            return {"enabled": True, "gray_scale": 1.0}
        
        flag_data = {
            "enabled": model.enabled,
            "gray_scale": model.gray_scale,
            "target_users": model.target_users,
            "metadata": model.metadata,
            "restore_at": model.restore_at.isoformat() if model.restore_at else None,
        }
        
        # 回寫 Redis
        await self._redis.setex(
            cache_key,
            self.REDIS_TTL,
            json.dumps(flag_data)
        )
        
        return flag_data
    
    async def is_enabled(self, name: str, platform: str | None = None, user_id: str | None = None) -> bool:
        """檢查開關是否啟用（支持灰度發布）
        
        Args:
            name: 開關名稱
            platform: 平台标识（可選）
            user_id: 用戶 ID（用於灰度分組）
        
        Returns:
            bool: 是否對該用戶/請求啟用
        """
        flag = await self.get_flag(name, platform)
        
        if not flag["enabled"]:
            return False
        
        # 檢查灰度發布
        gray_scale = flag.get("gray_scale", 1.0)
        if gray_scale < 1.0:
            # 目標用戶直接啟用
            if user_id and user_id in flag.get("target_users", []):
                return True
            
            # 按比例灰度（基於 user_id hash）
            if user_id:
                user_hash = hash(user_id) % 100
                return user_hash < (gray_scale * 100)
            
            # 無 user_id 時隨機
            import random
            return random.random() < gray_scale
        
        return True
    
    async def set_flag(
        self,
        name: str,
        enabled: bool,
        scope: FlagScope,
        platform: str | None = None,
        reason: str | None = None,
        changed_by: str | None = None,
        metadata: dict[str, Any] | None = None,
        restore_at: datetime | None = None,
        gray_scale: float | None = None,
    ) -> FeatureFlagModel:
        """設置開關狀態
        
        同時更新 Redis 和 PostgreSQL，並記錄審計日誌
        """
        # 查詢或創建
        query = select(FeatureFlagModel).where(FeatureFlagModel.name == name)
        if platform:
            query = query.where(FeatureFlagModel.platform == platform)
        
        result = await self._db.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            model = FeatureFlagModel(
                name=name,
                scope=scope.value,
                platform=platform,
                enabled=enabled,
                gray_scale=gray_scale or 1.0,
                metadata=metadata or {},
                restore_at=restore_at,
            )
            self._db.add(model)
        else:
            # 更新現有
            old_enabled = model.enabled
            model.enabled = enabled
            if gray_scale is not None:
                model.gray_scale = gray_scale
            if metadata is not None:
                model.metadata = metadata
            if restore_at is not None:
                model.restore_at = restore_at
            
            # 記錄審計日誌（僅在狀態變更時）
            if old_enabled != enabled:
                audit_log = FeatureFlagAuditLog(
                    flag_id=model.id,
                    old_value=old_enabled,
                    new_value=enabled,
                    reason=reason,
                    changed_by=changed_by or "system",
                )
                self._db.add(audit_log)
        
        await self._db.commit()
        await self._db.refresh(model)
        
        # 使 Redis 緩存失效
        cache_key = self._build_cache_key(name, platform)
        await self._redis.delete(cache_key)
        
        logger.info(
            "feature_flag.updated",
            name=name,
            platform=platform,
            enabled=enabled,
            reason=reason,
            changed_by=changed_by,
        )
        
        return model
    
    async def disable_platform(
        self,
        platform: str,
        reason: str | None = None,
        changed_by: str | None = None,
        auto_restore_minutes: int | None = None,
    ) -> None:
        """禁用整個平台的所有功能
        
        用於熔斷器觸發時的緊急降級
        """
        restore_at = None
        if auto_restore_minutes:
            restore_at = datetime.utcnow() + timedelta(minutes=auto_restore_minutes)
        
        # 禁用平台級開關
        await self.set_flag(
            name="platform_enabled",
            enabled=False,
            scope=FlagScope.PLATFORM,
            platform=platform,
            reason=reason,
            changed_by=changed_by,
            restore_at=restore_at,
            metadata={"auto_trigger": "circuit_breaker"},
        )
        
        logger.warning(
            "platform.disabled",
            platform=platform,
            reason=reason,
            restore_at=restore_at,
        )
    
    async def enable_platform(
        self,
        platform: str,
        reason: str | None = None,
        changed_by: str | None = None,
    ) -> None:
        """啟用平台"""
        await self.set_flag(
            name="platform_enabled",
            enabled=True,
            scope=FlagScope.PLATFORM,
            platform=platform,
            reason=reason,
            changed_by=changed_by,
        )
    
    async def list_flags(
        self,
        scope: FlagScope | None = None,
        platform: str | None = None,
        enabled_only: bool = False,
    ) -> list[dict[str, Any]]:
        """列出開關"""
        query = select(FeatureFlagModel)
        
        if scope:
            query = query.where(FeatureFlagModel.scope == scope.value)
        if platform:
            query = query.where(FeatureFlagModel.platform == platform)
        if enabled_only:
            query = query.where(FeatureFlagModel.enabled == True)
        
        query = query.order_by(FeatureFlagModel.created_at.desc())
        
        result = await self._db.execute(query)
        models = result.scalars().all()
        
        return [
            {
                "id": m.id,
                "name": m.name,
                "scope": m.scope,
                "platform": m.platform,
                "enabled": m.enabled,
                "gray_scale": m.gray_scale,
                "description": m.description,
                "metadata": m.metadata,
                "restore_at": m.restore_at.isoformat() if m.restore_at else None,
                "created_at": m.created_at.isoformat(),
                "updated_at": m.updated_at.isoformat(),
            }
            for m in models
        ]
    
    async def get_scheduled_restores(self) -> list[dict[str, Any]]:
        """獲取待恢復的平台列表"""
        now = datetime.utcnow()
        query = select(FeatureFlagModel).where(
            FeatureFlagModel.enabled == False,
            FeatureFlagModel.restore_at != None,
            FeatureFlagModel.restore_at <= now,
        )
        
        result = await self._db.execute(query)
        models = result.scalars().all()
        
        return [
            {
                "id": m.id,
                "name": m.name,
                "platform": m.platform,
                "restore_at": m.restore_at.isoformat(),
            }
            for m in models
        ]
    
    def _build_cache_key(self, name: str, platform: str | None) -> str:
        if platform:
            return f"{self.REDIS_PREFIX}:{platform}:{name}"
        return f"{self.REDIS_PREFIX}:global:{name}"


# 全局實例（通過依賴注入獲取）
_feature_flag_service: FeatureFlagService | None = None


def get_feature_flag_service(redis: Redis, db_session: AsyncSession) -> FeatureFlagService:
    """獲取服務實例"""
    global _feature_flag_service
    if _feature_flag_service is None:
        _feature_flag_service = FeatureFlagService(redis, db_session)
    return _feature_flag_service
