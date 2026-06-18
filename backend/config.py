"""SuperHub 配置管理"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    app_name: str = "SuperHub"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # 数据库配置
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "superhub_raw"
    
    postgresql_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/superhub"
    
    elasticsearch_url: str = "http://localhost:9200"
    
    # Redis/Celery 配置
    redis_url: str = "redis://localhost:6379/0"
    celery_broker: str = "redis://localhost:6379/1"
    celery_backend: str = "redis://localhost:6379/2"
    
    # 对象存储配置
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "superhub-media"
    minio_secure: bool = False
    
    # 熔断器配置 (可热更新)
    circuit_breaker_fail_max: int = Field(default=15, description="最大失败次数")
    circuit_breaker_reset_timeout: int = Field(default=300, description="重置超时(秒)")
    
    # 重试配置
    max_retries: int = 3
    retry_base_delay: float = 1.0
    
    # 账号池配置
    account_cooldown_seconds: int = 300
    account_max_failures: int = 5
    lease_timeout_seconds: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
