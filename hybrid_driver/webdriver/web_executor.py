from abc import ABC, abstractmethod
from typing import Optional, Any, List

import selenium
from selenium.webdriver.remote.webelement import WebElement


class WebExecutor(ABC):
    """Web 操作执行器基类"""
    
    @abstractmethod
    def connect(self, device_id: str, **kwargs) -> bool:
        """连接设备"""
        pass
    
    @abstractmethod
    def quit(self) -> None:
        """关闭连接"""
        pass
    
    @abstractmethod
    def is_alive(self) -> bool:
        """检查连接是否存活"""
        pass
    
    @abstractmethod
    def find_element(self, by: str, value: str) -> Optional[WebElement]:
        """查找元素"""
        pass

    @abstractmethod
    def find_elements(self, by: str, value: str) -> Optional[List[WebElement]]:
        """查找元素"""
        pass

    @abstractmethod
    def wait_for_element(self, by: str, value: str, timeout: int = 10) -> Optional[WebElement]:
        """等待元素出现"""
        pass
    
    @abstractmethod
    def execute_script(self, script: str, *args) -> Any:
        """执行 JavaScript"""
        pass
    
    @abstractmethod
    def get_current_url(self) -> str:
        """获取当前 URL"""
        pass
    
    @abstractmethod
    def get_page_source(self) -> str:
        """获取页面源码"""
        pass
    
    @abstractmethod
    def handle_common_popups(self) -> None:
        """处理常见弹窗"""
        pass
    
    @abstractmethod
    def get_window_handles(self) -> list:
        """获取所有窗口句柄"""
        pass
    
    @abstractmethod
    def switch_to_window(self, handle: str) -> None:
        """切换到指定窗口"""
        pass
    
    @abstractmethod
    def get_current_window_handle(self) -> str:
        """获取当前窗口句柄"""
        pass

    @abstractmethod
    def switch_to_new_window(self) -> None:
        pass

    @abstractmethod
    def get_visible_pages(self, timeout: int = 10) -> list:
        """获取可见页面列表"""
        pass

    def get_raw_remote_webdriver(self) -> selenium.webdriver.remote.webdriver.WebDriver:
        pass

