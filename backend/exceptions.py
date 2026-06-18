"""異常體系定義"""
from __future__ import annotations


class SuperHubError(Exception):
    """基類異常"""
    pass


class AdapterError(SuperHubError):
    """适配器层错误"""
    pass


class AuthenticationError(AdapterError):
    """认证失败"""
    pass


class RateLimitError(AdapterError):
    """频率限制"""
    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after: {retry_after}s")



class AccountPoolError(SuperHubError):
    """账号池错误"""
    pass


class NoAvailableAccountError(AccountPoolError):
    """无可用账号"""
    pass


class CircuitOpenError(SuperHubError):
    """熔断器打开"""
    pass


class SkipTask(SuperHubError):
    """跳过任务（用于功能开关控制）"""
    pass


class FeatureDisabledError(SuperHubError):
    """功能被禁用"""
    pass
