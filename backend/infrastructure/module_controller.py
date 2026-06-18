"""模塊控制器：在任務和適配器中檢查開關狀態"""
from __future__ import annotations

import structlog
from typing import Any
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.feature_flag import FeatureFlagService, FlagScope, get_feature_flag_service
from backend.exceptions import SkipTask, CircuitOpenError

logger = structlog.get_logger(__name__)


class ModuleController:
    """模塊控制器
    
    在 Celery 任務入口和 Adapter 關鍵步驟中檢查開關狀態，
    實現動態降級、精細化調度和資源隔離。
    
    使用示例:
    
    # Celery 任務中
    @shared_task
    def fetch_user_posts(platform, user_id):
        if not ModuleController.should_execute("posts", platform=platform):
            raise SkipTask(f"Posts feature disabled for {platform}")
        ...
    
    # Adapter 中
    async def fetch_live_stream(self, room_id):
        if not await ModuleController.is_feature_enabled("live", self.platform):
            raise FeatureDisabledError("Live streaming not enabled")
        ...
    """
    
    _service: FeatureFlagService | None = None
    
    @classmethod
    def initialize(cls, redis: Redis, db_session: AsyncSession) -> None:
        """初始化服務實例"""
        cls._service = get_feature_flag_service(redis, db_session)
    
    @classmethod
    def _get_service(cls) -> FeatureFlagService:
        if cls._service is None:
            raise RuntimeError("ModuleController not initialized. Call initialize() first.")
        return cls._service
    
    @classmethod
    async def should_execute(
        cls,
        feature: str,
        platform: str | None = None,
        task_id: str | None = None,
        user_id: str | None = None,
    ) -> bool:
        """檢查任務是否應該執行
        
        檢查順序：
        1. 全局開關 (global.all_enabled)
        2. 平台開關 (platform.{platform}.platform_enabled)
        3. 功能開關 (feature.{platform}.{feature})
        4. 策略開關 (strategy.{strategy_name})
        
        Returns:
            bool: True=允許執行，False=跳過
        """
        service = cls._get_service()
        
        # 1. 檢查全局開關
        global_enabled = await service.is_enabled("all_enabled")
        if not global_enabled:
            logger.warning(
                "task.skipped.global_disabled",
                task_id=task_id,
                platform=platform,
                feature=feature,
            )
            return False
        
        # 2. 檢查平台開關
        if platform:
            platform_enabled = await service.is_enabled("platform_enabled", platform=platform)
            if not platform_enabled:
                logger.warning(
                    "task.skipped.platform_disabled",
                    task_id=task_id,
                    platform=platform,
                    feature=feature,
                )
                return False
        
        # 3. 檢查功能開關
        if platform and feature:
            feature_enabled = await service.is_enabled(feature, platform=platform)
            if not feature_enabled:
                logger.warning(
                    "task.skipped.feature_disabled",
                    task_id=task_id,
                    platform=platform,
                    feature=feature,
                )
                return False
        
        # 4. 檢查策略開關（如果有）
        # 例如：new_parser, aggressive_mode 等
        # 可在 metadata 中配置需要的策略
        
        return True
    
    @classmethod
    async def is_feature_enabled(
        cls,
        feature: str,
        platform: str,
    ) -> bool:
        """簡化版：僅檢查平台和功能開關
        
        用於 Adapter 內部快速判斷
        """
        service = cls._get_service()
        
        # 先檢查平台
        platform_ok = await service.is_enabled("platform_enabled", platform=platform)
        if not platform_ok:
            return False
        
        # 再檢查具體功能
        return await service.is_enabled(feature, platform=platform)
    
    @classmethod
    async def check_and_raise(
        cls,
        feature: str,
        platform: str | None = None,
        task_id: str | None = None,
    ) -> None:
        """檢查開關，如果禁用則拋出異常
        
        用於需要明確錯誤場景的代碼
        """
        enabled = await cls.should_execute(feature, platform, task_id)
        if not enabled:
            raise SkipTask(
                f"Feature '{feature}' is disabled" + (f" for platform '{platform}'" if platform else "")
            )
    
    @classmethod
    async def get_platform_status(cls, platform: str) -> dict[str, Any]:
        """獲取平台的完整狀態信息
        
        Returns:
            dict: {
                "enabled": bool,
                "features": {"posts": bool, "live": bool, ...},
                "gray_scale": float,
                "restore_at": str | None,
            }
        """
        service = cls._get_service()
        
        platform_flag = await service.get_flag("platform_enabled", platform=platform)
        
        # 獲取各功能狀態
        features = {}
        for feature in ["posts", "live", "comments", "search"]:
            flag = await service.get_flag(feature, platform=platform)
            features[feature] = flag["enabled"]
        
        return {
            "enabled": platform_flag["enabled"],
            "features": features,
            "gray_scale": platform_flag.get("gray_scale", 1.0),
            "restore_at": platform_flag.get("restore_at"),
        }


# 便捷函數
async def should_execute(*args, **kwargs) -> bool:
    return await ModuleController.should_execute(*args, **kwargs)


async def is_feature_enabled(*args, **kwargs) -> bool:
    return await ModuleController.is_feature_enabled(*args, **kwargs)
