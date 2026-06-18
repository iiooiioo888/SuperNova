"""适配器注册表"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseAdapter


_adapter_registry: dict[str, type["BaseAdapter"]] = {}


def register_adapter(platform_name: str):
    """适配器注册装饰器"""
    def decorator(cls: type["BaseAdapter"]) -> type["BaseAdapter"]:
        _adapter_registry[platform_name] = cls
        return cls
    return decorator


def get_adapter(platform: str) -> "BaseAdapter":
    """获取指定平台的适配器实例"""
    from .exceptions import UnknownPlatformError
    
    cls = _adapter_registry.get(platform)
    if not cls:
        raise UnknownPlatformError(platform)
    return cls()


def list_adapters() -> list[str]:
    """列出所有已注册的适配器"""
    return list(_adapter_registry.keys())
