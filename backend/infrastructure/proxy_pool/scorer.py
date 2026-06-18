"""代理评分器"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ProxyScoreFactors:
    """代理评分因子"""
    latency_weight: float = 0.3
    success_rate_weight: float = 0.4
    recency_weight: float = 0.3


class ProxyScorer:
    """代理质量评分器
    
    根据延迟、成功率和最近使用时间综合评分。
    """

    def __init__(self, factors: ProxyScoreFactors | None = None):
        self._factors = factors or ProxyScoreFactors()

    def calculate_score(
        self,
        latency_ms: float | None,
        success_count: int,
        failure_count: int,
        last_used_seconds_ago: float | None,
    ) -> float:
        """计算代理综合评分 (0.0 - 1.0)"""
        # 延迟评分 (越低越好，500ms 以下满分)
        if latency_ms is not None:
            latency_score = max(0.0, 1.0 - latency_ms / 5000.0)
        else:
            latency_score = 0.5  # 未知延迟给中间分

        # 成功率评分
        total = success_count + failure_count
        if total > 0:
            success_rate = success_count / total
        else:
            success_rate = 0.5  # 无历史数据给中间分

        # 新鲜度评分 (越近越好，1小时内满分)
        if last_used_seconds_ago is not None:
            recency_score = max(0.0, 1.0 - last_used_seconds_ago / 3600.0)
        else:
            recency_score = 1.0  # 从未使用过也给满分

        # 加权平均
        score = (
            latency_score * self._factors.latency_weight
            + success_rate * self._factors.success_rate_weight
            + recency_score * self._factors.recency_weight
        )
        return round(min(1.0, max(0.0, score)), 4)

    def rank_proxies(self, proxies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """对代理列表评分排序"""
        for proxy in proxies:
            proxy["_score"] = self.calculate_score(
                latency_ms=proxy.get("latency_ms"),
                success_count=proxy.get("success_count", 0),
                failure_count=proxy.get("failure_count", 0),
                last_used_seconds_ago=proxy.get("last_used_seconds_ago"),
            )
        return sorted(proxies, key=lambda p: p["_score"], reverse=True)


# 全局单例
proxy_scorer = ProxyScorer()
