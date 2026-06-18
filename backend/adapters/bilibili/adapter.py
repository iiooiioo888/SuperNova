"""Bilibili 适配器实现"""
from __future__ import annotations

import structlog
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, AsyncIterator

import httpx

from ..base import (
    BaseAdapter,
    FetchParams,
    UnifiedPost,
    UnifiedProfile,
    UnifiedComment,
    MediaRef,
    EngagementMetrics,
    UnifiedDanmaku,
    UnifiedLiveStream,
)
from ..registry import register_adapter
from ...exceptions import AuthenticationError, RateLimitError
from ...utils.fingerprint import get_browser_fingerprint

logger = structlog.get_logger()

# B 站 API 基础配置
BILIBILI_API = {
    "user_info": "https://api.bilibili.com/x/space/wbi/acc/info",
    "user_videos": "https://api.bilibili.com/x/space/wbi/arc/search",
    "video_info": "https://api.bilibili.com/x/web-interface/view",
    "comments": "https://api.bilibili.com/x/v2/reply",
    "search": "https://api.bilibili.com/x/web-interface/search/type",
    "live_info": "https://api.live.bilibili.com/room/v1/Room/get_info",
    "live_danmaku": "https://api.live.bilibili.com/xlive/web-room/v1/dM/gethistory",
}


@register_adapter("bilibili")
class BilibiliAdapter(BaseAdapter):
    """Bilibili 平台适配器"""

    platform = "bilibili"

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def setup(self) -> None:
        """初始化 HTTP 会话"""
        headers = get_browser_fingerprint("chrome")
        headers["Referer"] = "https://www.bilibili.com"
        self._client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )
        logger.info("bilibili_adapter.setup", platform=self.platform)

    async def teardown(self) -> None:
        """清理资源"""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("bilibili_adapter.teardown", platform=self.platform)

    async def _request(self, url: str, params: dict | None = None) -> dict[str, Any]:
        """统一请求方法，带错误处理"""
        if not self._client:
            raise RuntimeError("Adapter not initialized. Call setup() first.")

        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != 0:
                code = data.get("code")
                msg = data.get("message", "Unknown error")
                if code == -412:
                    raise RateLimitError(retry_after=60)
                if code == -101:
                    raise AuthenticationError("Bilibili login required")
                logger.warning("bilibili_api.error", url=url, code=code, message=msg)
                return {}

            return data.get("data", {})

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 412:
                raise RateLimitError(retry_after=120)
            raise
        except httpx.RequestError as e:
            logger.error("bilibili_api.request_error", url=url, error=str(e))
            raise

    async def fetch_user_profile(self, user_id: str) -> UnifiedProfile:
        """获取 B 站用户资料"""
        logger.info("bilibili_adapter.fetch_user_profile", user_id=user_id)

        data = await self._request(BILIBILI_API["user_info"], {"mid": user_id})

        return UnifiedProfile(
            platform=self.platform,
            platform_user_id=user_id,
            username=data.get("name", f"user_{user_id}"),
            display_name=data.get("name"),
            bio=data.get("sign"),
            avatar_url=data.get("face"),
            follower_count=data.get("follower"),
            is_verified=data.get("official", {}).get("role", 0) > 0,
            extra={
                "level": data.get("level"),
                "vip": data.get("vip", {}).get("status", 0),
            },
        )

    async def fetch_posts(
        self, target: str, params: FetchParams
    ) -> AsyncIterator[UnifiedPost]:
        """获取 B 站视频列表"""
        logger.info("bilibili_adapter.fetch_posts", target=target, limit=params.limit)

        page = 1
        fetched = 0
        while fetched < params.limit:
            data = await self._request(
                BILIBILI_API["user_videos"],
                {"mid": target, "ps": min(50, params.limit - fetched), "pn": page},
            )
            vlist = data.get("list", {}).get("vlist", [])
            if not vlist:
                break

            for v in vlist:
                yield UnifiedPost(
                    platform=self.platform,
                    platform_post_id=v.get("bvid", ""),
                    author_id=target,
                    author_name=v.get("author", ""),
                    content_type="video",
                    text=v.get("title", ""),
                    media=[],
                    metrics=EngagementMetrics(
                        views=v.get("play", 0),
                        comments=v.get("comment", 0),
                    ),
                    published_at=datetime.fromtimestamp(v.get("created", 0), tz=UTC) if v.get("created") else None,
                    url=f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                )
                fetched += 1
                if fetched >= params.limit:
                    break

            page += 1

    async def fetch_comments(
        self, post_id: str, params: FetchParams
    ) -> AsyncIterator[UnifiedComment]:
        """获取视频评论"""
        logger.info("bilibili_adapter.fetch_comments", post_id=post_id)

        page = 1
        fetched = 0
        while fetched < params.limit:
            data = await self._request(
                BILIBILI_API["comments"],
                {"type": 1, "oid": post_id, "pn": page, "ps": min(20, params.limit - fetched)},
            )
            replies = data.get("replies") or []
            if not replies:
                break

            for r in replies:
                member = r.get("member", {})
                yield UnifiedComment(
                    platform=self.platform,
                    platform_comment_id=str(r.get("rpid", "")),
                    platform_post_id=post_id,
                    author_id=member.get("mid", ""),
                    author_name=member.get("uname", ""),
                    text=r.get("content", {}).get("message", ""),
                    likes=r.get("like", 0),
                    published_at=datetime.fromtimestamp(r.get("ctime", 0), tz=UTC) if r.get("ctime") else None,
                )
                fetched += 1
                if fetched >= params.limit:
                    break

            page += 1

    async def download_media(
        self, media: MediaRef, dest: Path
    ) -> Path:
        """下载 B 站媒体文件"""
        logger.info("bilibili_adapter.download_media", media_id=media.platform_media_id)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if not self._client:
            raise RuntimeError("Adapter not initialized")

        async with self._client.stream("GET", media.url) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size=8192):
                    f.write(chunk)

        return dest

    async def search(
        self, query: str, params: FetchParams
    ) -> AsyncIterator[UnifiedPost]:
        """搜索 B 站内容"""
        logger.info("bilibili_adapter.search", query=query)

        data = await self._request(
            BILIBILI_API["search"],
            {"keyword": query, "search_type": "video", "page": 1, "pagesize": params.limit},
        )
        results = data.get("result") or []

        for v in results:
            yield UnifiedPost(
                platform=self.platform,
                platform_post_id=v.get("bvid", ""),
                author_id=str(v.get("mid", "")),
                author_name=v.get("author", ""),
                content_type="video",
                text=v.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                metrics=EngagementMetrics(views=v.get("play", 0)),
                url=f"https://www.bilibili.com/video/{v.get('bvid', '')}",
            )

    # ── 直播相关方法重写 ───────────────────────────────────────

    async def fetch_live_stream(self, live_id: str) -> UnifiedLiveStream | None:
        """获取 B 站直播流信息"""
        logger.info("bilibili_adapter.fetch_live_stream", live_id=live_id)

        data = await self._request(BILIBILI_API["live_info"], {"room_id": live_id})
        if not data:
            return None

        uid = data.get("uid", "")
        return UnifiedLiveStream(
            platform=self.platform,
            platform_live_id=str(data.get("room_id", live_id)),
            author_id=str(uid),
            author_name=data.get("anchor_info", {}).get("base_info", {}).get("uname", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status="live" if data.get("live_status") == 1 else "ended",
            viewer_count=data.get("online", 0),
            cover_url=data.get("user_cover"),
        )

    async def fetch_danmaku(
        self, live_id: str, params: FetchParams
    ) -> AsyncIterator[UnifiedDanmaku]:
        """获取 B 站直播弹幕"""
        logger.info("bilibili_adapter.fetch_danmaku", live_id=live_id, limit=params.limit)

        data = await self._request(BILIBILI_API["live_danmaku"], {"roomid": live_id})
        dms = data.get("room") or []

        for dm in dms[:params.limit]:
            yield UnifiedDanmaku(
                platform=self.platform,
                platform_danmaku_id=str(dm.get("id", "")),
                platform_live_id=live_id,
                author_id=str(dm.get("uid", "")),
                author_name=dm.get("nickname", ""),
                text=dm.get("text", ""),
                published_at=datetime.fromtimestamp(dm.get("timeline", 0), tz=UTC) if dm.get("timeline") else datetime.now(UTC),
            )

    def capabilities(self) -> list:
        """B 站特有能力"""
        from ..base import Capability

        return [
            Capability(
                name="fetch_danmaku",
                description="获取弹幕数据",
                params_schema={"video_id": {"type": "string"}},
                returns_schema={"danmaku_list": {"type": "array"}},
            ),
            Capability(
                name="fetch_video_info",
                description="获取视频详细信息",
                params_schema={"bvid": {"type": "string"}},
                returns_schema={"video_info": {"type": "object"}},
            ),
        ]

    async def invoke(self, capability_name: str, **kwargs) -> Any:
        """调用 B 站特有能力"""
        if capability_name == "fetch_danmaku":
            return await self._fetch_danmaku(**kwargs)
        elif capability_name == "fetch_video_info":
            return await self._fetch_video_info(**kwargs)
        return await super().invoke(capability_name, **kwargs)

    async def _fetch_danmaku(self, video_id: str) -> list[dict]:
        """获取弹幕（内部实现）"""
        logger.info("bilibili_adapter.fetch_danmaku", video_id=video_id)
        # TODO: 实现弹幕获取（需要解析 protobuf）
        return []

    async def _fetch_video_info(self, bvid: str) -> dict:
        """获取视频信息（内部实现）"""
        logger.info("bilibili_adapter.fetch_video_info", bvid=bvid)
        data = await self._request(BILIBILI_API["video_info"], {"bvid": bvid})
        return data or {}
