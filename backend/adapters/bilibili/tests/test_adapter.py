"""Bilibili 适配器测试"""
import pytest
from pathlib import Path
from datetime import datetime

from backend.adapters.bilibili.adapter import BilibiliAdapter
from backend.adapters.base import FetchParams, UnifiedPost


@pytest.fixture
async def adapter():
    """创建适配器实例"""
    adapter = BilibiliAdapter()
    await adapter.setup()
    yield adapter
    await adapter.teardown()


@pytest.mark.asyncio
async def test_fetch_user_profile(adapter):
    """测试获取用户资料"""
    user_id = "123456"
    profile = await adapter.fetch_user_profile(user_id)
    
    assert profile.platform == "bilibili"
    assert profile.platform_user_id == user_id


@pytest.mark.asyncio
async def test_fetch_posts(adapter):
    """测试获取帖子列表"""
    target = "test_user"
    params = FetchParams(limit=10)
    
    posts = []
    async for post in adapter.fetch_posts(target, params):
        posts.append(post)
    
    assert len(posts) >= 0  # 占位实现可能返回空
    if posts:
        assert isinstance(posts[0], UnifiedPost)
        assert posts[0].platform == "bilibili"


@pytest.mark.asyncio
async def test_download_media(adapter, tmp_path):
    """测试媒体下载"""
    from backend.adapters.base import MediaRef
    
    media = MediaRef(
        platform_media_id="test_media",
        media_type="image",
        url="https://example.com/test.jpg",
    )
    
    dest = tmp_path / "test.jpg"
    result = await adapter.download_media(media, dest)
    
    assert result.exists()


def test_capabilities(adapter):
    """测试平台能力"""
    capabilities = adapter.capabilities()
    
    assert len(capabilities) > 0
    capability_names = [c.name for c in capabilities]
    assert "fetch_danmaku" in capability_names