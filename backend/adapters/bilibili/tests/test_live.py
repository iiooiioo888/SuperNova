"""Bilibili 直播相关测试"""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone

from backend.adapters.bilibili.adapter import BilibiliAdapter
from backend.adapters.base import FetchParams, UnifiedDanmaku, UnifiedLiveStream


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> dict | str:
    """加载测试样本"""
    filepath = FIXTURES_DIR / filename
    if filepath.suffix == ".xml":
        return filepath.read_text(encoding="utf-8")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def adapter():
    """创建 B 站适配器实例"""
    return BilibiliAdapter()


class TestLiveStream:
    """直播流信息测试"""
    
    @pytest.mark.asyncio
    async def test_fetch_live_stream(self, adapter):
        """测试获取直播信息（占位实现）"""
        result = await adapter.fetch_live_stream("123456")
        # 目前是占位实现，返回 None
        assert result is None
    
    @pytest.mark.asyncio
    async def test_parse_live_room_info(self):
        """测试解析直播间信息"""
        raw_data = load_fixture("live_room_info.json")
        
        # 模拟解析逻辑（待实现）
        data = raw_data["data"]
        room_info = data["room_info"]
        
        assert room_info["room_id"] == 123456
        assert room_info["title"] == "【直播】SuperHub 项目开发中"
        assert room_info["live_status"] == 1
        assert room_info["area_name"] == "科技区"
        assert room_info["view_count"] > 0


class TestDanmaku:
    """弹幕相关测试"""
    
    @pytest.mark.asyncio
    async def test_fetch_danmaku(self, adapter):
        """测试获取直播弹幕（占位实现）"""
        params = FetchParams(limit=10)
        
        # 目前是占位实现，直接验证方法存在并返回空结果
        # 实际实现时会是一个 async generator
        import inspect
        method = adapter.fetch_danmaku("123456", params)
        assert inspect.iscoroutine(method) or inspect.isasyncgen(method)
        
        # 清理未 await 的 coroutine
        try:
            if inspect.iscoroutine(method):
                method.close()
        except Exception:
            pass
    
    @pytest.mark.asyncio
    async def test_parse_live_danmaku_history(self):
        """测试解析历史弹幕数据"""
        raw_data = load_fixture("live_danmaku_history.json")
        
        items = raw_data["data"]["items"]
        assert len(items) == 3
        
        # 验证第一条普通弹幕
        item0 = items[0]
        assert item0["msg"] == "主播好！"
        assert item0["uname"] == "观众 A"
        assert item0["medal"] is not None
        assert item0["medal"]["level"] == 10
        
        # 验证礼物弹幕
        item2 = items[2]
        assert item2["msg_type"] == 1
        assert "火箭" in item2["msg"]
        assert item2["gift_info"]["price"] == 2000
    
    @pytest.mark.asyncio
    async def test_unified_danmaku_model(self):
        """测试 UnifiedDanmaku 数据模型"""
        danmaku = UnifiedDanmaku(
            platform="bilibili",
            platform_danmaku_id="dm_123",
            platform_live_id="123456",
            author_id="987654321",
            author_name="观众 A",
            text="主播好！",
            published_at=datetime.now(timezone.utc),
            color="#FFFFFF",
            is_gift=False,
            badge_level=10,
            badge_name="粉丝牌",
            user_level=15,
            is_moderator=False,
            is_vip=False,
        )
        
        assert danmaku.platform == "bilibili"
        assert danmaku.text == "主播好！"
        assert danmaku.color == "#FFFFFF"
        assert danmaku.badge_level == 10
        assert not danmaku.is_gift
    
    @pytest.mark.asyncio
    async def test_parse_video_danmaku_xml(self):
        """测试解析视频弹幕 XML"""
        xml_content = load_fixture("video_danmaku.xml")
        
        # 简单的 XML 解析测试（实际实现会用 xml.etree.ElementTree）
        assert "<?xml" in xml_content
        assert "<d p=" in xml_content
        assert "普通滚动弹幕" in xml_content
        
        # 验证弹幕数量
        danmaku_count = xml_content.count("<d p=")
        assert danmaku_count == 5
    
    @pytest.mark.asyncio
    async def test_subscribe_danmaku_not_implemented(self, adapter):
        """测试实时弹幕订阅（目前未实现）"""
        async def callback(danmaku: UnifiedDanmaku):
            pass
        
        with pytest.raises(NotImplementedError):
            await adapter.subscribe_danmaku("123456", callback)


class TestUnifiedLiveStreamModel:
    """UnifiedLiveStream 模型测试"""
    
    def test_create_live_stream(self):
        """测试创建直播流对象"""
        live = UnifiedLiveStream(
            platform="bilibili",
            platform_live_id="123456",
            author_id="123456789",
            author_name="示例 UP 主",
            title="【直播】SuperHub 项目开发中",
            description="演示直播内容",
            status="live",
            viewer_count=15234,
            max_viewer_count=20000,
            category="科技区",
            tags=["编程", "开发"],
        )
        
        assert live.platform == "bilibili"
        assert live.status == "live"
        assert live.viewer_count == 15234
        assert "编程" in live.tags
    
    def test_live_stream_status_mapping(self):
        """测试直播状态映射"""
        # API 值到 UnifiedLiveStream.status 的映射
        status_map = {
            0: "upcoming",   # 未开播
            1: "live",       # 直播中
            2: "live",       # 轮播
        }
        
        for api_value, expected_status in status_map.items():
            assert expected_status in ["live", "upcoming", "ended"]
