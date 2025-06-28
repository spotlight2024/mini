"""
pytest配置文件
提供测试夹具和配置
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from hybrid_driver.device_pool import DevicePool
from hybrid_driver.device.android_device import AndroidDevice
from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor
from hybrid_driver.webdriver.appium_executor import AppiumExecutor


@pytest.fixture
def device_pool():
    """设备池测试夹具"""
    pool = DevicePool()
    yield pool
    # 清理设备池 - 使用__exit__方法
    pool.__exit__(None, None, None)


@pytest.fixture
def mock_device():
    """模拟设备测试夹具"""
    device = AndroidDevice("test_device")
    # 模拟WebExecutor
    device._web_execute = Mock()
    yield device
    # 清理设备连接
    if hasattr(device, 'disconnect'):
        device.disconnect()


@pytest.fixture
def mock_selenium_executor():
    """模拟Selenium执行器测试夹具"""
    executor = SeleniumWebExecutor()
    # 模拟WebDriver - 使用正确的属性名
    executor._driver = Mock()
    yield executor
    # 清理执行器
    if hasattr(executor, 'quit'):
        executor.quit()


@pytest.fixture
def mock_appium_executor():
    """模拟Appium执行器测试夹具"""
    # 提供默认参数
    executor = AppiumExecutor("http://localhost:4723", {})
    # 模拟WebDriver
    executor.driver = Mock()
    yield executor
    # 清理执行器
    if hasattr(executor, 'quit'):
        executor.quit()


@pytest.fixture
def mock_web_element():
    """模拟WebElement测试夹具"""
    element = Mock()
    element.click = Mock(return_value=None)
    element.send_keys = Mock(return_value=None)
    element.text = "Test Element"
    element.get_attribute = Mock(return_value="test-value")
    return element


@pytest.fixture
def test_context():
    """测试上下文夹具"""
    return {
        'element': None,
        'result': None,
        'data': {}
    }


# pytest配置
def pytest_configure(config):
    """pytest配置"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "functional: 功能测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    for item in items:
        # 为测试文件添加标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "functional" in str(item.fspath):
            item.add_marker(pytest.mark.functional) 