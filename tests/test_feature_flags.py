"""功能開關系統測試"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from backend.services.feature_flag import FeatureFlagService, FlagScope
from backend.infrastructure.module_controller import ModuleController
from backend.exceptions import SkipTask


@pytest.fixture
def mock_redis():
    """Mock Redis 客戶端"""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def mock_db_session():
    """Mock DB Session"""
    session = AsyncMock()
    
    # Mock execute 返回結果
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    
    session.execute = AsyncMock(return_value=result)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    
    return session


@pytest.mark.asyncio
async def test_get_flag_not_exists(mock_redis, mock_db_session):
    """獲取不存在的開關，應返回默認啟用"""
    service = FeatureFlagService(mock_redis, mock_db_session)
    
    flag = await service.get_flag("non_existent")
    
    assert flag["enabled"] is True
    assert flag["gray_scale"] == 1.0


@pytest.mark.asyncio
async def test_is_enabled_with_gray_scale(mock_redis, mock_db_session):
    """測試灰度發布邏輯"""
    service = FeatureFlagService(mock_redis, mock_db_session)
    
    # Mock 返回 50% 灰度
    mock_redis.get = AsyncMock(return_value=b'{"enabled": true, "gray_scale": 0.5, "target_users": []}')
    
    # 測試不同 user_id 的灰度分組
    results = []
    for i in range(100):
        enabled = await service.is_enabled("test_feature", user_id=f"user_{i}")
        results.append(enabled)
    
    # 約 50% 啟用
    enabled_count = sum(results)
    assert 40 <= enabled_count <= 60  # 允許一定波動


@pytest.mark.asyncio
async def test_is_enabled_target_user(mock_redis, mock_db_session):
    """測試目標用戶白名單"""
    service = FeatureFlagService(mock_redis, mock_db_session)
    
    # Mock 返回 10% 灰度但包含特定用戶
    mock_redis.get = AsyncMock(
        return_value=b'{"enabled": true, "gray_scale": 0.1, "target_users": ["vip_user_123"]}'
    )
    
    # 白名單用戶應始終啟用
    enabled = await service.is_enabled("test_feature", user_id="vip_user_123")
    assert enabled is True
    
    # 普通用戶只有 10% 概率
    mock_redis.get = AsyncMock(return_value=b'{"enabled": true, "gray_scale": 0.1, "target_users": []}')
    results = []
    for i in range(100):
        enabled = await service.is_enabled("test_feature", user_id=f"user_{i}")
        results.append(enabled)
    
    enabled_count = sum(results)
    assert 5 <= enabled_count <= 15


@pytest.mark.asyncio
async def test_disable_platform(mock_redis, mock_db_session):
    """測試禁用平台"""
    service = FeatureFlagService(mock_redis, mock_db_session)
    
    await service.disable_platform(
        platform="bilibili",
        reason="測試禁用",
        changed_by="test_user",
        auto_restore_minutes=30,
    )
    
    # 驗證 DB 操作
    assert mock_db_session.add.called
    assert mock_db_session.commit.called
    
    # 驗證 Redis 緩存失效
    assert mock_redis.delete.called


@pytest.mark.asyncio
async def test_module_controller_should_execute(mock_redis, mock_db_session):
    """測試模塊控制器檢查邏輯"""
    # 初始化控制器
    ModuleController.initialize(mock_redis, mock_db_session)
    
    # Mock 所有開關為啟用
    mock_redis.get = AsyncMock(
        return_value=b'{"enabled": true, "gray_scale": 1.0}'
    )
    
    # 應允許執行
    should_run = await ModuleController.should_execute("posts", platform="bilibili")
    assert should_run is True


@pytest.mark.asyncio
async def test_module_controller_platform_disabled(mock_redis, mock_db_session):
    """測試平台禁用時任務跳過"""
    ModuleController.initialize(mock_redis, mock_db_session)
    
    # Mock 平台開關為禁用
    async def mock_get(key):
        if "bilibili:platform_enabled" in key:
            return b'{"enabled": false, "gray_scale": 1.0}'
        return b'{"enabled": true, "gray_scale": 1.0}'
    
    mock_redis.get = AsyncMock(side_effect=mock_get)
    
    # 應跳過執行
    should_run = await ModuleController.should_execute("posts", platform="bilibili")
    assert should_run is False


@pytest.mark.asyncio
async def test_check_and_raise(mock_redis, mock_db_session):
    """測試檢查並拋出異常"""
    ModuleController.initialize(mock_redis, mock_db_session)
    
    # Mock 功能禁用
    mock_redis.get = AsyncMock(
        return_value=b'{"enabled": false, "gray_scale": 1.0}'
    )
    
    with pytest.raises(SkipTask) as exc_info:
        await ModuleController.check_and_raise("live", platform="bilibili")
    
    assert "live" in str(exc_info.value)
    assert "bilibili" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_scheduled_restores(mock_redis, mock_db_session):
    """測試獲取待恢復任務"""
    service = FeatureFlagService(mock_redis, mock_db_session)
    
    # Mock DB 返回待恢復記錄
    mock_model = MagicMock()
    mock_model.id = 1
    mock_model.name = "platform_enabled"
    mock_model.platform = "bilibili"
    mock_model.restore_at = datetime.utcnow() - timedelta(minutes=1)  # 已到期
    
    result = MagicMock()
    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_model])))
    mock_db_session.execute = AsyncMock(return_value=result)
    
    restores = await service.get_scheduled_restores()
    
    assert len(restores) == 1
    assert restores[0]["platform"] == "bilibili"


print("\n✅ 所有功能開關測試用例如上")
