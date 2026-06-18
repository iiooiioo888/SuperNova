"""代理池服务"""
from __future__ import annotations

import structlog
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

logger = structlog.get_logger(__name__)


@dataclass
class ProxyInfo:
    """代理信息"""
    proxy_id: str
    url: str  # http://host:port or socks5://host:port
    protocol: str = "http"  # http, https, socks5
    username: str | None = None
    password: str | None = None
    score: float = 1.0  # 0.0-1.0 评分
    latency_ms: float | None = None
    success_count: int = 0
    failure_count: int = 0
    last_used_at: datetime | None = None
    is_active: bool = True
    region: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def auth_url(self) -> str:
        """返回带认证信息的代理 URL"""
        if self.username and self.password:
            protocol = self.protocol
            return f"{protocol}://{self.username}:{self.password}@{self.url.split('://')[-1]}"
        return self.url


class ProxyPoolService:
    """代理池服务"""

    def __init__(self):
        self._proxies: dict[str, ProxyInfo] = {}

    async def get_proxy(self, platform: str | None = None) -> ProxyInfo | None:
        """获取最优代理"""
        available = [
            p for p in self._proxies.values()
            if p.is_active and p.score > 0.1
        ]
        if not available:
            return None
        available.sort(key=lambda p: p.score, reverse=True)
        return available[0]

    async def report_success(self, proxy_id: str, latency_ms: float | None = None) -> None:
        """报告代理使用成功"""
        proxy = self._proxies.get(proxy_id)
        if proxy:
            proxy.success_count += 1
            proxy.last_used_at = datetime.now(UTC)
            if latency_ms is not None:
                proxy.latency_ms = latency_ms
            proxy.score = min(1.0, proxy.score + 0.05)

    async def report_failure(self, proxy_id: str) -> None:
        """报告代理使用失败"""
        proxy = self._proxies.get(proxy_id)
        if proxy:
            proxy.failure_count += 1
            proxy.last_used_at = datetime.now(UTC)
            proxy.score = max(0.0, proxy.score - 0.2)
            if proxy.score <= 0.1:
                proxy.is_active = False
                logger.warning("proxy_pool.proxy_deactivated", proxy_id=proxy_id)

    async def add_proxy(self, proxy: ProxyInfo) -> None:
        """添加代理"""
        self._proxies[proxy.proxy_id] = proxy
        logger.info("proxy_pool.proxy_added", proxy_id=proxy.proxy_id)

    async def remove_proxy(self, proxy_id: str) -> bool:
        """移除代理"""
        if proxy_id in self._proxies:
            del self._proxies[proxy_id]
            return True
        return False

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        total = len(self._proxies)
        active = sum(1 for p in self._proxies.values() if p.is_active)
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
        }


# 全局单例
proxy_pool_service = ProxyPoolService()
