# SuperHub 架构决策记录

本目录包含所有重要的架构决策记录（Architecture Decision Records, ADR）。

## ADR 列表

- [001: 选择 Celery 而非 Airflow 作为任务调度器](decisions/001-celery-over-airflow.md)
- [002: 三层存储架构设计](decisions/002-three-layer-storage.md)
- [003: 账号租约模型设计](decisions/003-account-lease-model.md)

## 什么是 ADR？

ADR 是一种记录重要架构决策及其背景的文档格式。每个 ADR 包含：

- **状态**: 提议 / 已接受 / 已废弃 / 已替换
- **背景**: 为什么需要做这个决策
- **决策**: 我们决定做什么
- **结果**: 这个决策带来的后果（正面和负面）

参考：[Michael Nygard 的 ADR 模板](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
