"""MongoDB 原始数据存储"""
from __future__ import annotations

import structlog
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Any

from ..config import settings

logger = structlog.get_logger()


class RawStore:
    """MongoDB 原始数据存储"""
    
    def __init__(self):
        self._client: AsyncIOMotorClient | None = None
        self._db = None
    
    async def connect(self) -> None:
        """连接数据库"""
        self._client = AsyncIOMotorClient(settings.mongodb_url)
        self._db = self._client[settings.mongodb_db]
        logger.info("mongodb.connected", url=settings.mongodb_url, db=settings.mongodb_db)
    
    async def disconnect(self) -> None:
        """断开连接"""
        if self._client:
            self._client.close()
            logger.info("mongodb.disconnected")
    
    async def store_raw_response(
        self,
        platform: str,
        data_type: str,
        data_id: str,
        response: dict[str, Any],
    ) -> str:
        """存储原始响应"""
        collection = self._db[f"{platform}_{data_type}_raw"]
        
        document = {
            "platform": platform,
            "data_type": data_type,
            "data_id": data_id,
            "response": response,
            "collected_at": datetime.utcnow(),
        }
        
        result = await collection.insert_one(document)
        logger.info("mongodb.stored", platform=platform, data_type=data_type, data_id=data_id)
        return str(result.inserted_id)
    
    async def get_raw_responses(
        self,
        platform: str,
        data_type: str,
        limit: int = 100,
    ) -> list[dict]:
        """获取原始响应"""
        collection = self._db[f"{platform}_{data_type}_raw"]
        
        cursor = collection.find(
            {"platform": platform, "data_type": data_type},
            sort=[("collected_at", -1)],
            limit=limit,
        )
        
        return await cursor.to_list(length=limit)


# 全局单例
raw_store = RawStore()
