#!/usr/bin/env python3
"""初始化数据库 Schema。

使用方法:
    python -m scripts.init_db
"""
import asyncio
import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.models.pg import Base

logger = structlog.get_logger(__name__)


async def init_postgresql():
    """初始化 PostgreSQL 数据库。"""
    logger.info("Initializing PostgreSQL...")
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("PostgreSQL tables created successfully")
    
    await engine.dispose()


async def init_mongodb():
    """初始化 MongoDB 数据库（创建索引）。"""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    logger.info("Initializing MongoDB...")
    
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client.get_default_database()
    
    # 创建 Raw 层集合索引
    # 示例：raw_bilibili_posts
    collections = [
        ("raw_bilibili_posts", [("ingested_at", -1), ("platform", 1)]),
        ("raw_bilibili_comments", [("ingested_at", -1), ("platform", 1)]),
        ("raw_douyin_posts", [("ingested_at", -1), ("platform", 1)]),
        ("raw_weibo_posts", [("ingested_at", -1), ("platform", 1)]),
        ("raw_instagram_posts", [("ingested_at", -1), ("platform", 1)]),
        ("raw_telegram_posts", [("ingested_at", -1), ("platform", 1)]),
    ]
    
    for collection_name, indexes in collections:
        collection = db[collection_name]
        for index in indexes:
            await collection.create_index(index)
        logger.info(f"Created indexes for {collection_name}")
    
    client.close()
    logger.info("MongoDB initialized successfully")


async def main():
    """主函数。"""
    logger.info("Starting database initialization...")
    
    try:
        await init_postgresql()
        await init_mongodb()
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
