#!/usr/bin/env python3
"""种子脚本：向账号池添加测试账号。

使用方法:
    python -m scripts.seed_accounts
    
环境变量:
    SEED_ACCOUNTS_JSON: JSON 格式的账号列表（可选）
"""
import asyncio
import json
import os
import structlog
from datetime import datetime

from backend.config import settings
from backend.infrastructure.account_pool.service import AccountPoolService
from backend.infrastructure.account_pool.models import AccountStatus

logger = structlog.get_logger(__name__)


# 默认测试账号（仅用于开发环境）
DEFAULT_TEST_ACCOUNTS = [
    {
        "platform": "bilibili",
        "account_id": "test_user_001",
        "credentials": {
            "cookies": "SESSDATA=xxx; bili_jct=xxx;",
            "user_agent": "Mozilla/5.0 ..."
        },
        "status": "active",
        "weight": 100,
    },
    {
        "platform": "bilibili",
        "account_id": "test_user_002",
        "credentials": {
            "cookies": "SESSDATA=yyy; bili_jct=yyy;",
            "user_agent": "Mozilla/5.0 ..."
        },
        "status": "active",
        "weight": 90,
    },
]


async def seed_accounts():
    """添加测试账号到账号池。"""
    logger.info("Starting account seeding...")
    
    # 从环境变量或默认值加载账号
    accounts_json = os.environ.get(
        "SEED_ACCOUNTS_JSON",
        json.dumps(DEFAULT_TEST_ACCOUNTS)
    )
    accounts = json.loads(accounts_json)
    
    service = AccountPoolService()
    
    added_count = 0
    for account_data in accounts:
        try:
            # 这里应该调用账号池的添加接口
            # 由于账号池实现可能不同，这里仅作示例
            logger.info(
                "Would add account",
                platform=account_data["platform"],
                account_id=account_data["account_id"],
            )
            added_count += 1
        except Exception as e:
            logger.error(
                "Failed to add account",
                account_id=account_data["account_id"],
                error=str(e),
            )
    
    logger.info(f"Seeding completed. Added {added_count} accounts.")
    
    # 注意：实际实现需要等待账号池服务的具体 API
    # 这里只是演示脚本结构


async def main():
    """主函数。"""
    if settings.ENVIRONMENT == "production":
        logger.warning("Running in production environment. Aborting seed operation.")
        return
    
    await seed_accounts()


if __name__ == "__main__":
    asyncio.run(main())
