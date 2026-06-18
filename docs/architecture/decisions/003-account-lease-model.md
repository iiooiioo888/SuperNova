# ADR 003: 账号租约模型设计

**日期**: 2024-01-15  
**状态**: 已接受  
**决策者**: SuperHub Team

## 背景

多平台数据采集需要管理大量账号凭证，面临以下挑战：

1. **并发安全**: 多个任务不能同时使用同一个账号
2. **故障恢复**: 任务崩溃后需要释放账号，防止永久占用
3. **状态管理**: 账号可能处于 active / cooldown / banned 等状态
4. **权重分配**: 优质账号应该优先分配给重要任务
5. **审计追踪**: 需要记录哪个任务在什么时间使用了哪个账号

## 决策

**采用租约（Lease）模型管理账号**，而非简单的"借用 - 归还"模式。

### 核心概念

```python
@dataclass
class AccountLease:
    lease_id: str              # 租约 ID（UUID）
    platform: str              # 平台标识
    credentials: dict          # 账号凭证（cookies, tokens 等）
    account_id: str            # 账号 ID
    acquired_at: datetime      # 租用时间
    expires_at: datetime       # 过期时间（默认 10 分钟）
```

### 接口设计

```python
class AccountPoolService:
    async def acquire(self, platform: str, task_type: str) -> AccountLease
    async def report_success(self, lease: AccountLease) -> None
    async def report_failure(self, lease: AccountLease, error_type: str) -> None
    async def release(self, lease: AccountLease) -> None
    async def health_check(self, platform: str) -> dict
```

### 状态机

```
active ──失败──► cooldown ──冷却完成──► active
  │                                        │
  │           连续失败达阈值               │
  └────────────► banned                    │
                    ▲                      │
                    └──────────────────────┘
```

### 关键设计决策

1. **租约超时自动释放**: 
   - Lease 包含 `expires_at` 字段
   - 后台定时任务扫描过期租约并释放
   - 防止任务崩溃导致账号永久占用

2. **权重评分系统**:
   - 每个账号维护权重分数（初始 100）
   - 成功采集 +10 分，失败 -20 分
   - 高分账号优先分配
   - 低于阈值（如 30 分）进入 cooldown 状态

3. **错误类型差异化处理**:
   - `RateLimitError`: 账号进入 cooldown，冷却时间根据错误信息调整
   - `AuthenticationError`: 账号标记为 banned，需要人工介入
   - `NetworkError`: 不扣分，重试其他账号
   - `ContentNotFoundError`: 不扣分，记录状态

## 结果

### 正面影响

1. **容错性**: 任务崩溃不会导致账号永久锁定
2. **公平性**: 权重系统确保优质账号不被滥用
3. **可观测性**: 租约记录便于追踪账号使用情况
4. **简单性**: 三状态机易于理解和实现

### 负面影响

1. **复杂性**: 相比简单的"借用 - 归还"，需要维护租约表和定时任务
2. **延迟**: 租约过期扫描有延迟（默认 1 分钟），可能导致账号短暂不可用

### 缓解措施

- 租约到期时间设置为任务预计耗时的 2-3 倍
- 定时任务每分钟扫描一次过期租约
- 提供手动释放接口，用于紧急情况

## 未来优化方向

1. **温度分层**: 将账号分为 hot/warm/cold，不同层级采用不同策略
2. **养号逻辑**: 模拟真实用户行为，提高账号存活率
3. **智能调度**: 根据平台风控策略动态调整账号分配
4. **凭证轮换**: 自动刷新 Cookie/Token，减少人工介入

## 参考

- [AWS Kinesis Client Library Lease Model](https://docs.aws.amazon.com/streams/latest/dev/kinesis-record-processor-lease-management.html)
- [Distributed Locks with Redis](https://redis.io/topics/distlock)
