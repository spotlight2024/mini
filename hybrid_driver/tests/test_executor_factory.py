"""
执行器工厂测试
验证新的架构设计是否正常工作
"""

import pytest
from unittest.mock import Mock, patch
from hybrid_driver.webdriver.executor_factory import ExecutorFactory, executor_factory
from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor
from hybrid_driver.webdriver.appium_executor import AppiumExecutor
from hybrid_driver.webdriver.web_executor import WebExecutor


class TestExecutorFactory:
    """执行器工厂测试类"""
    
    def test_get_available_executors(self):
        """测试获取可用执行器列表"""
        executors = executor_factory.get_available_executors()
        assert "selenium" in executors
        assert "appium" in executors
        assert len(executors) >= 2
    
    def test_get_selenium_executor(self):
        """测试获取 Selenium 执行器"""
        executor = executor_factory.get_executor("selenium")
        assert isinstance(executor, SeleniumWebExecutor)
        assert executor._driver is None
    
    def test_get_appium_executor(self):
        """测试获取 Appium 执行器"""
        executor = executor_factory.get_executor(
            "appium",
            appium_server_url="http://localhost:4723",
            capabilities={"platformName": "Android"}
        )
        assert isinstance(executor, AppiumExecutor)
        assert executor._appium_server_url == "http://localhost:4723"
        assert executor._capabilities["platformName"] == "Android"
    
    def test_get_unknown_executor(self):
        """测试获取未知执行器"""
        with pytest.raises(ValueError, match="未知的执行器类型"):
            executor_factory.get_executor("unknown")
    
    def test_register_custom_executor(self):
        """测试注册自定义执行器"""
        class CustomExecutor(WebExecutor):
            def connect(self, device_id: str, **kwargs) -> bool:
                return True
            
            def quit(self) -> None:
                pass
            
            def is_alive(self) -> bool:
                return True
            
            def find_element(self, by: str, value: str):
                return None
            
            def find_elements(self, by: str, value: str):
                return None
            
            def wait_for_element(self, by: str, value: str, timeout: int = 10):
                return None
            
            def execute_script(self, script: str, *args):
                return None
            
            def get_current_url(self) -> str:
                return ""
            
            def get_page_source(self) -> str:
                return ""
            
            def handle_common_popups(self) -> None:
                pass
            
            def get_window_handles(self) -> list:
                return []
            
            def switch_to_window(self, handle: str) -> None:
                pass
            
            def get_current_window_handle(self) -> str:
                return ""
            
            def switch_to_new_window(self) -> None:
                pass
        
        # 注册自定义执行器
        executor_factory.register_executor("custom", CustomExecutor)
        
        # 验证注册成功
        executors = executor_factory.get_available_executors()
        assert "custom" in executors
        
        # 测试获取自定义执行器
        executor = executor_factory.get_executor("custom")
        assert isinstance(executor, CustomExecutor)


class TestBackwardCompatibility:
    """向后兼容性测试"""
    
    def test_android_device_default_executor(self):
        """测试 AndroidDevice 默认使用 Selenium"""
        from hybrid_driver.device.android_device import AndroidDevice
        
        # 不指定执行器类型，应该默认使用 Selenium
        device = AndroidDevice(serial_id="test_device")
        assert device._executor_type == "selenium"
        assert device._web_execute_cls is None
    
    def test_android_device_custom_executor_type(self):
        """测试 AndroidDevice 指定执行器类型"""
        from hybrid_driver.device.android_device import AndroidDevice
        
        # 指定执行器类型
        device = AndroidDevice(
            serial_id="test_device",
            executor_type="appium",
            appium_server_url="http://localhost:4723"
        )
        assert device._executor_type == "appium"
        assert device._executor_kwargs["appium_server_url"] == "http://localhost:4723"
    
    def test_android_device_legacy_web_execute_cls(self):
        """测试 AndroidDevice 使用传统的 web_execute_cls 参数"""
        from hybrid_driver.device.android_device import AndroidDevice
        from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor
        
        # 使用传统的 web_execute_cls 参数
        device = AndroidDevice(
            serial_id="test_device",
            web_execute_cls=SeleniumWebExecutor
        )
        assert device._web_execute_cls == SeleniumWebExecutor
        assert device._executor_type == "selenium"  # 默认值


class TestExecutorIntegration:
    """执行器集成测试"""
    
    @patch('hybrid_driver.webdriver.selenium_executor.connect_webdriver')
    def test_selenium_executor_connect(self, mock_connect):
        """测试 Selenium 执行器连接"""
        # 模拟 WebDriver
        mock_driver = Mock()
        mock_connect.return_value = mock_driver
        
        executor = SeleniumWebExecutor()
        success = executor.connect("test_device")
        
        assert success is True
        assert executor._driver == mock_driver
        assert executor._device_id == "test_device"
    
    @patch('appium.webdriver.Remote')
    def test_appium_executor_connect(self, mock_remote):
        """测试 Appium 执行器连接"""
        # 模拟 Appium WebDriver
        mock_driver = Mock()
        mock_remote.return_value = mock_driver
        
        executor = AppiumExecutor(
            appium_server_url="http://localhost:4723",
            capabilities={"platformName": "Android"}
        )
        success = executor.connect("test_device")
        
        assert success is True
        assert executor.driver == mock_driver


if __name__ == "__main__":
    pytest.main([__file__]) 