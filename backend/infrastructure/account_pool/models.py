"""账号池数据模型"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from backend.config import settings


class AccountState(str, Enum):
    """账号状态"""
    ACTIVE = "active"
    COOLDOWN = "cooldown"
    BANNED = "banned"


@dataclass
class AccountLease:
    """账号租约"""
    lease_id: str
    platform: str
    credentials: dict[str, Any]  # cookies, tokens, headers 等
    account_id: str
    acquired_at: datetime
    expires_at: datetime
    
    @classmethod
    def create(
        cls,
        platform: str,
        account_id: str,
        credentials: dict[str, Any],
        timeout_seconds: int = None,
    ) -> "AccountLease":
        """创建新租约"""
        if timeout_seconds is None:
            timeout_seconds = settings.lease_timeout_seconds
        
        now = datetime.utcnow()
        return cls(
            lease_id=str(uuid.uuid4()),
            platform=platform,
            credentials=credentials,
            account_id=account_id,
            acquired_at=now,
            expires_at=now + timedelta(seconds=timeout_seconds),
        )
    
    def is_expired(self) -> bool:
        """检查租约是否过期"""
        return datetime.utcnow() > self.expires_at


@dataclass
class Account:
    """账号实体"""
    account_id: str
    platform: str
    credentials: dict[str, Any]
    state: AccountState = AccountState.ACTIVE
    failure_count: int = 0
    weight: float = 1.0  # 权重分数
    last_used_at: datetime | None = None
    cooldown_until: datetime | None = None
    
    def can_use(self) -> bool:
        """检查账号是否可用"""
        if self.state == AccountState.BANNED:
            return False
        if self.state == AccountState.COOLDOWN:
            if self.cooldown_until and datetime.utcnow() < self.cooldown_until:
                return False
            # 冷却时间已过，恢复为 active
            self.state = AccountState.ACTIVE
            self.cooldown_until = None
        return True
    
    def mark_success(self) -> None:
        """标记成功使用"""
        self.failure_count = 0
        self.last_used_at = datetime.utcnow()
        # 轻微提升权重
        self.weight = min(1.0, self.weight + 0.01)
    
    def mark_failure(self, max_failures: int = None, cooldown_seconds: int = None) -> None:
        """标记失败"""
        if max_failures is None:
            max_failures = settings.account_max_failures
        if cooldown_seconds is None:
            cooldown_seconds = settings.account_cooldown_seconds
        
        self.failure_count += 1
        self.last_used_at = datetime.utcnow()
        
        if self.failure_count >= max_failures:
            self.state = AccountState.BANNED
        else:
            self.state = AccountState.COOLDOWN
            self.cooldown_until = datetime.utcnow() + timedelta(seconds=cooldown_seconds)
        
        # 降低权重
        self.weight = max(0.0, self.weight - 0.1)
