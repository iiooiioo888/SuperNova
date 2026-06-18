"""熔断器封装"""
import structlog
import pybreaker

logger = structlog.get_logger()


class CircuitBreakerManager:
    """熔断器管理器"""
    
    def __init__(self):
        self._breakers: dict[str, pybreaker.CircuitBreaker] = {}
    
    def get_breaker(
        self,
        platform: str,
        fail_max: int = 15,
        reset_timeout: int = 300,
    ) -> pybreaker.CircuitBreaker:
        """获取或创建平台的熔断器"""
        if platform not in self._breakers:
            self._breakers[platform] = pybreaker.CircuitBreaker(
                fail_max=fail_max,
                reset_timeout=reset_timeout,
                name=f"{platform}_circuit",
            )
            logger.info("circuit_breaker.created", platform=platform, fail_max=fail_max)
        
        return self._breakers[platform]
    
    def get_status(self, platform: str) -> dict | None:
        """获取平台熔断器状态"""
        breaker = self._breakers.get(platform)
        if not breaker:
            return None
        
        return {
            "platform": platform,
            "state": breaker.current_state,
            "fail_count": breaker.fail_count,
            "fail_max": breaker.fail_max,
        }
    
    def list_all(self) -> list[dict]:
        """列出所有熔断器状态"""
        return [
            self.get_status(platform)
            for platform in self._breakers.keys()
        ]


# 全局单例
circuit_breaker_manager = CircuitBreakerManager()


def platform_circuit(platform: str, fail_max: int = 15, reset_timeout: int = 300):
    """平台熔断器装饰器（支持 sync 和 async 函数）"""
    import asyncio
    breaker = circuit_breaker_manager.get_breaker(platform, fail_max, reset_timeout)
    
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @breaker
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @breaker
            def sync_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return sync_wrapper
    return decorator
