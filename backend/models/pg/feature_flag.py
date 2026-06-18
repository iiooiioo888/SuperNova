"""PostgreSQL 數據模型：功能開關與審計日誌"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Real,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.models.pg.base import Base


class FeatureFlagModel(Base):
    """功能開關模型
    
    支持四層控制：
    - scope='global': platform=NULL, 全局緊急制動
    - scope='platform': platform='bilibili', name='platform_enabled'
    - scope='feature': platform='bilibili', name='posts'|'live'|'comments'
    - scope='strategy': platform=NULL, name='new_parser'|'aggressive_mode'
    """
    __tablename__ = "feature_flags"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # global|platform|feature|strategy
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 灰度發布相關
    gray_scale: Mapped[float] = mapped_column(Real, default=1.0, nullable=False)  # 0.0-1.0
    target_users: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)  # 白名單用戶
    
    # 元數據
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    # 定時恢復
    restore_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # 審計字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    
    # 關聯
    audit_logs: Mapped[list["FeatureFlagAuditLog"]] = relationship(
        "FeatureFlagAuditLog",
        back_populates="flag",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<FeatureFlag(name={self.name}, platform={self.platform}, enabled={self.enabled})>"


class FeatureFlagAuditLog(Base):
    """功能開關變更審計日誌
    
    記錄每次開關狀態變更的詳細信息，用於追溯和合規
    """
    __tablename__ = "feature_flag_audit_logs"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    flag_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("feature_flags.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # 變更前後值
    old_value: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    new_value: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
    # 變更原因
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 操作者信息
    changed_by: Mapped[str] = mapped_column(String(128), nullable=False)  # user_id or 'system'
    changed_from: Mapped[str | None] = mapped_column(String(64), nullable=True)  # IP address
    
    # 自動觸發標記
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trigger_source: Mapped[str | None] = mapped_column(String(64), nullable=True)  # circuit_breaker|scheduled_restore|...
    
    # 時間
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    
    # 關聯
    flag: Mapped["FeatureFlagModel"] = relationship("FeatureFlagModel", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<FeatureFlagAuditLog(flag_id={self.flag_id}, {self.old_value}->{self.new_value})>"
