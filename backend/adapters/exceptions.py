"""适配器异常"""
from backend.exceptions import AdapterError


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
