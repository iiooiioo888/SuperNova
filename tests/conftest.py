"""测试配置"""
import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# pytest-asyncio 配置
pytest_plugins = ["pytest_asyncio"]
