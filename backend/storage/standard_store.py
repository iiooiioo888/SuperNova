"""PostgreSQL 标准化数据存储"""
from __future__ import annotations

import structlog
from datetime import datetime, UTC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class StandardStore:
    """PostgreSQL 标准化数据存储
    
    将采集到的原始数据标准化后存入 PostgreSQL，
    提供结构化查询能力。
    """

    def __init__(self):
        self._session: AsyncSession | None = None

    async def store_post(
        self,
        db: AsyncSession,
        platform: str,
        platform_post_id: str,
        author_id: str,
        author_name: str | None,
        content_type: str,
        text: str,
        metrics: dict[str, Any],
        tags: list[str],
        published_at: datetime | None,
        raw_data: dict[str, Any],
    ) -> dict[str, Any]:
        """存储标准化帖子数据"""
        document = {
            "platform": platform,
            "platform_post_id": platform_post_id,
            "author_id": author_id,
            "author_name": author_name,
            "content_type": content_type,
            "text": text,
            "metrics": metrics,
            "tags": tags,
            "published_at": published_at.isoformat() if published_at else None,
            "collected_at": datetime.now(UTC).isoformat(),
            "raw_data": raw_data,
        }
        # TODO: 实际写入 PostgreSQL
        logger.info(
            "standard_store.post_stored",
            platform=platform,
            post_id=platform_post_id,
        )
        return document

    async def store_profile(
        self,
        db: AsyncSession,
        platform: str,
        platform_user_id: str,
        username: str,
        display_name: str | None,
        follower_count: int | None,
        following_count: int | None,
        post_count: int | None,
        is_verified: bool,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        """存储标准化用户资料"""
        document = {
            "platform": platform,
            "platform_user_id": platform_user_id,
            "username": username,
            "display_name": display_name,
            "follower_count": follower_count,
            "following_count": following_count,
            "post_count": post_count,
            "is_verified": is_verified,
            "extra": extra,
            "collected_at": datetime.now(UTC).isoformat(),
        }
        logger.info(
            "standard_store.profile_stored",
            platform=platform,
            user_id=platform_user_id,
        )
        return document

    async def store_comment(
        self,
        db: AsyncSession,
        platform: str,
        platform_comment_id: str,
        platform_post_id: str,
        author_id: str,
        author_name: str | None,
        text: str,
        likes: int,
        reply_to_comment_id: str | None,
        published_at: datetime | None,
    ) -> dict[str, Any]:
        """存储标准化评论"""
        document = {
            "platform": platform,
            "platform_comment_id": platform_comment_id,
            "platform_post_id": platform_post_id,
            "author_id": author_id,
            "author_name": author_name,
            "text": text,
            "likes": likes,
            "reply_to_comment_id": reply_to_comment_id,
            "published_at": published_at.isoformat() if published_at else None,
            "collected_at": datetime.now(UTC).isoformat(),
        }
        logger.info(
            "standard_store.comment_stored",
            platform=platform,
            comment_id=platform_comment_id,
        )
        return document


# 全局单例
standard_store = StandardStore()
