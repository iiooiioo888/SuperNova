"""账号池服务"""
from __future__ import annotations

import structlog
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from backend.config import settings

logger = structlog.get_logger()


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
            logger.warning("account.banned", account_id=self.account_id, platform=self.platform)
        else:
            self.state = AccountState.COOLDOWN
            self.cooldown_until = datetime.utcnow() + timedelta(seconds=cooldown_seconds)
            logger.info("account.cooldown", account_id=self.account_id, platform=self.platform)
        
        # 降低权重
        self.weight = max(0.0, self.weight - 0.1)


class AccountPoolService:
    """账号池服务"""
    
    def __init__(self):
        # 内存存储，Phase 1 简化实现
        # TODO: Phase 2 迁移到 Redis/PostgreSQL
        self._accounts: dict[str, dict[str, Account]] = {}  # platform -> {account_id -> Account}
        self._leases: dict[str, AccountLease] = {}  # lease_id -> AccountLease
    
    async def acquire(self, platform: str, task_type: str = "default") -> AccountLease:
        """获取账号租约"""
        logger.info("account_pool.acquire", platform=platform, task_type=task_type)
        
        platform_accounts = self._accounts.get(platform, {})
        
        # 选择权重最高的可用账号
        available = [
            acc for acc in platform_accounts.values()
            if acc.can_use()
        ]
        
        if not available:
            from ..exceptions import NoAvailableAccountError
            raise NoAvailableAccountError(f"No available account for platform: {platform}")
        
        # 按权重排序
        available.sort(key=lambda x: x.weight, reverse=True)
        account = available[0]
        
        lease = AccountLease.create(
            platform=platform,
            account_id=account.account_id,
            credentials=account.credentials,
        )
        
        self._leases[lease.lease_id] = lease
        account.last_used_at = datetime.utcnow()
        
        logger.info("account_pool.leased", lease_id=lease.lease_id, account_id=account.account_id)
        return lease
    
    async def report_success(self, lease: AccountLease) -> None:
        """报告使用成功"""
        logger.info("account_pool.success", lease_id=lease.lease_id)
        
        platform_accounts = self._accounts.get(lease.platform, {})
        account = platform_accounts.get(lease.account_id)
        
        if account:
            account.mark_success()
    
    async def report_failure(self, lease: AccountLease, error_type: str) -> None:
        """报告使用失败"""
        logger.warning("account_pool.failure", lease_id=lease.lease_id, error_type=error_type)
        
        platform_accounts = self._accounts.get(lease.platform, {})
        account = platform_accounts.get(lease.account_id)
        
        if account:
            account.mark_failure()
    
    async def release(self, lease: AccountLease) -> None:
        """释放租约"""
        logger.info("account_pool.release", lease_id=lease.lease_id)
        self._leases.pop(lease.lease_id, None)
    
    async def health_check(self, platform: str) -> dict:
        """健康检查"""
        platform_accounts = self._accounts.get(platform, {})
        
        total = len(platform_accounts)
        active = sum(1 for acc in platform_accounts.values() if acc.state == AccountState.ACTIVE)
        cooldown = sum(1 for acc in platform_accounts.values() if acc.state == AccountState.COOLDOWN)
        banned = sum(1 for acc in platform_accounts.values() if acc.state == AccountState.BANNED)
        
        return {
            "platform": platform,
            "total": total,
            "active": active,
            "cooldown": cooldown,
            "banned": banned,
        }
    
    async def add_account(
        self,
        platform: str,
        account_id: str,
        credentials: dict[str, Any],
    ) -> None:
        """添加账号到池中（用于测试和初始化）"""
        if platform not in self._accounts:
            self._accounts[platform] = {}
        
        self._accounts[platform][account_id] = Account(
            account_id=account_id,
            platform=platform,
            credentials=credentials,
        )
        logger.info("account_pool.added", platform=platform, account_id=account_id)


# 全局单例
account_pool_service = AccountPoolService()
