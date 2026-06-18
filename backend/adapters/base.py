"""适配器基础接口和数据模型"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator
from pathlib import Path


# ── 统一数据模型 ──────────────────────────────────────────

@dataclass
class MediaRef:
    """媒体引用"""
    platform_media_id: str
    media_type: str  # "image" | "video" | "audio" | "document"
    url: str
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    file_size_bytes: int | None = None


@dataclass
class EngagementMetrics:
    """互动指标"""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    saves: int = 0
    platform_specific: dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedPost:
    """统一帖子模型"""
    platform: str
    platform_post_id: str
    author_id: str
    author_name: str | None = None
    content_type: str  # "text" | "image" | "video" | "story" | "reel"
    text: str = ""
    media: list[MediaRef] = field(default_factory=list)
    metrics: EngagementMetrics = field(default_factory=EngagementMetrics)
    tags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    language: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    collected_at: datetime = field(default_factory=datetime.utcnow)
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedProfile:
    """统一用户资料模型"""
    platform: str
    platform_user_id: str
    username: str
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    follower_count: int | None = None
    following_count: int | None = None
    post_count: int | None = None
    is_verified: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UnifiedComment:
    """统一评论模型"""
    platform: str
    platform_comment_id: str
    platform_post_id: str
    author_id: str
    author_name: str | None = None
    text: str = ""
    likes: int = 0
    reply_to_comment_id: str | None = None
    published_at: datetime | None = None
    collected_at: datetime = field(default_factory=datetime.utcnow)


# ── 采集参数 ──────────────────────────────────────────────

@dataclass
class FetchParams:
    """采集参数"""
    limit: int = 50
    cursor: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    include_comments: bool = False
    max_depth: int = 1


# ── 能力描述 ──────────────────────────────────────────────

@dataclass
class Capability:
    """平台特有能力"""
    name: str
    description: str
    params_schema: dict[str, Any]
    returns_schema: dict[str, Any]


# ── 基类 ─────────────────────────────────────────────────

class BaseAdapter(ABC):
    """适配器基类"""
    
    platform: str  # 子类必须定义
    
    # -- 标准模式（所有平台必须实现）--
    
    @abstractmethod
    async def fetch_user_profile(self, user_id: str) -> UnifiedProfile:
        """获取用户资料"""
        ...
    
    @abstractmethod
    async def fetch_posts(
        self, target: str, params: FetchParams
    ) -> AsyncIterator[UnifiedPost]:
        """获取帖子列表，支持分页游标"""
        ...
    
    @abstractmethod
    async def fetch_comments(
        self, post_id: str, params: FetchParams
    ) -> AsyncIterator[UnifiedComment]:
        """获取评论列表"""
        ...
    
    @abstractmethod
    async def download_media(
        self, media: MediaRef, dest: Path
    ) -> Path:
        """下载媒体文件到指定路径"""
        ...
    
    @abstractmethod
    async def search(
        self, query: str, params: FetchParams
    ) -> AsyncIterator[UnifiedPost]:
        """搜索公开内容"""
        ...
    
    # -- 高级模式（平台特有功能）--
    
    def capabilities(self) -> list[Capability]:
        """返回平台特有能力列表，默认为空"""
        return []
    
    async def invoke(self, capability_name: str, **kwargs) -> Any:
        """调用平台特有能力"""
        from .exceptions import CapabilityNotSupported
        
        supported = {c.name for c in self.capabilities()}
        if capability_name not in supported:
            raise CapabilityNotSupported(capability_name, self.platform)
        raise NotImplementedError
    
    # -- 生命周期 --
    
    async def setup(self) -> None:
        """初始化时调用，用于建立连接、验证凭证等"""
        pass
    
    async def teardown(self) -> None:
        """清理资源"""
        pass
