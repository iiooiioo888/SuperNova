"""结构化日志配置"""
import structlog
from structlog.types import Processor


def setup_logging() -> None:
    """配置 structlog"""
    
    # 共享处理器
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
    ]
    
    # 开发环境格式化输出
    structlog.configure(
        processors=shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger("INFO"),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """获取 logger 实例"""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()