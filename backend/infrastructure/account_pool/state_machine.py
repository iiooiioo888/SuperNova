"""账号状态机"""
from __future__ import annotations

from enum import Enum
from typing import Any


class AccountState(str, Enum):
    """账号状态"""
    ACTIVE = "active"
    COOLDOWN = "cooldown"
    BANNED = "banned"


# 状态转换规则
VALID_TRANSITIONS: dict[AccountState, set[AccountState]] = {
    AccountState.ACTIVE: {AccountState.COOLDOWN, AccountState.BANNED},
    AccountState.COOLDOWN: {AccountState.ACTIVE, AccountState.BANNED},
    AccountState.BANNED: set(),  # 终态，不可转换
}


def can_transition(current: AccountState, target: AccountState) -> bool:
    """检查状态转换是否合法"""
    return target in VALID_TRANSITIONS.get(current, set())


def transition(current: AccountState, target: AccountState) -> AccountState:
    """执行状态转换，不合法则抛出异常"""
    if not can_transition(current, target):
        raise ValueError(
            f"Invalid state transition: {current.value} -> {target.value}"
        )
    return target
