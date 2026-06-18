"""SuperHub 异常体系"""


class SuperHubError(Exception):
    """基类异常"""
    pass


class AdapterError(SuperHubError):
    """适配器层错误"""
    pass


class AuthenticationError(AdapterError):
    """认证失败"""
    pass


class RateLimitError(AdapterError):
    """频率限制"""
    
    def __init__(self, retry_after: int | None = None, message: str = "Rate limit exceeded"):
        self.retry_after = retry_after
        super().__init__(message)


class CapabilityNotSupported(AdapterError):
    """调用不支持的能力"""
    
    def __init__(self, capability_name: str, platform: str):
        self.capability_name = capability_name
        self.platform = platform
        super().__init__(f"Capability '{capability_name}' not supported on platform '{platform}'")


class UnknownPlatformError(AdapterError):
    """未知平台"""
    
    def __init__(self, platform: str):
        self.platform = platform
        super().__init__(f"Unknown platform: {platform}")


class AccountPoolError(SuperHubError):
    """账号池错误"""
    pass


class NoAvailableAccountError(AccountPoolError):
    """无可用账号"""
    pass


class CircuitOpenError(SuperHubError):
    """熔断器打开"""
    
    def __init__(self, platform: str):
        self.platform = platform
        super().__init__(f"Circuit breaker open for platform: {platform}")


class StorageError(SuperHubError):
    """存储层错误"""
    pass


class ProxyError(SuperHubError):
    """代理错误"""
    pass
