from typing import Optional, Any, Dict, Type

import adbutils
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from hybrid_driver.log_config import get_logger
from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor
from hybrid_driver.webdriver.web_executor import WebExecutor

# 获取logger实例
logger = get_logger(__name__)


class AndroidDevice:
    """Android 设备类"""
    
    def __init__(self, serial_id: str, web_execute_cls: Type[WebExecutor] = SeleniumWebExecutor):
        self._serial_id = serial_id
        self._web_execute: Optional[WebExecutor] = None
        self._web_execute_cls = web_execute_cls
        self._status = "disconnected"  # connected/disconnected
        self.adb_device = adbutils.adb.device(serial=self._serial_id)
    
    def connect(self, **kwargs) -> bool:
        """连接设备"""
        try:
            logger.info(f"尝试通过 adb 查找设备 serial_id={self._serial_id}")
            if not self.adb_device:
                logger.error(f"adb 未找到设备 serial_id={self._serial_id}")
                self._status = "disconnected"
                return False
            logger.info(f"adb 设备已找到 serial_id={self._serial_id}")

            # 初始化 WebExecutor
            logger.info(f"准备初始化 WebExecutor，serial_id={self._serial_id}")
            self._web_execute = self._web_execute_cls()
            if not self._web_execute.connect(self._serial_id, **kwargs):
                logger.error(f"WebExecutor 初始化失败 serial_id={self._serial_id}")
                self._status = "disconnected"
                return False
            
            logger.info(f"WebExecutor 初始化成功 serial_id={self._serial_id}")
            self._status = "connected"
            return True
        except Exception as e:
            logger.exception(f"连接设备 serial_id={self._serial_id} 发生异常: {e}")
            self._status = "disconnected"
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        if self._web_execute:
            try:
                logger.info(f"关闭 WebExecutor serial_id={self._serial_id}")
                self._web_execute.quit()
            except Exception as e:
                logger.error(f"关闭 WebExecutor 发生异常 serial_id={self._serial_id}: {e}")
            finally:
                self._web_execute = None
        self._status = "disconnected"
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        try:
            device = adbutils.adb.device(serial=self._serial_id)
            alive = device is not None and self._web_execute is not None
            return alive
        except Exception as e:
            logger.error(f"检查设备存活异常 serial_id={self._serial_id}: {e}")
            return False

    def wait_for_page_load(self, timeout: int = 10) -> bool:
        """等待页面加载完成"""
        if not self.is_connected():
            return False
        return self._web_execute.wait_for_page_load(timeout)
    
    def wait_for_new_window(self, timeout: int = 10, old_handles: Optional[set] = None) -> Optional[str]:
        """等待新窗口出现"""
        if not self.is_connected():
            return None
        return self._web_execute.wait_for_new_window(timeout, old_handles)

    def switch_to_new_window(self) -> None:
        """<UNK>"""
        if not self.is_connected():
            return None
        self._web_execute.switch_to_new_window()
        return None

    def find_element(self, by: str, value: str) -> Optional[WebElement]:
        """查找元素"""
        if not self.is_connected():
            return None
        return self._web_execute.find_element(by, value)

    def find_elements(self, by: str, value: str) -> Optional[WebElement]:
        """查找元素"""
        if not self.is_connected():
            return None
        return self._web_execute.find_elements(by, value)

    def wait_for_element(self, by: str, value: str, timeout: int = 10) -> Optional[WebElement]:
        """等待元素出现"""
        if not self.is_connected():
            return None
        return self._web_execute.wait_for_element(by, value, timeout)
    
    def execute_script(self, script: str, *args) -> Any:
        """执行 JavaScript"""
        if not self.is_connected():
            return None
        return self._web_execute.execute_script(script, *args)
    
    def get_current_url(self) -> str:
        """获取当前 URL"""
        if not self.is_connected():
            return ""
        return self._web_execute.get_current_url()
    
    def get_page_source(self) -> str:
        """获取页面源码"""
        if not self.is_connected():
            return ""
        return self._web_execute.get_page_source()
    
    def handle_common_popups(self) -> None:
        """处理常见弹窗"""
        if not self.is_connected():
            return
        self._web_execute.handle_common_popups()
    
    def get_window_handles(self) -> list:
        """获取所有窗口句柄"""
        if not self.is_connected():
            return []
        return self._web_execute.get_window_handles()
    
    def switch_to_window(self, handle: str) -> None:
        """切换到指定窗口"""
        if not self.is_connected():
            return
        self._web_execute.switch_to_window(handle)
    
    def get_current_window_handle(self) -> str:
        """获取当前窗口句柄"""
        if not self.is_connected():
            return ""
        return self._web_execute.get_current_window_handle()
    
    def do_action(self, action_type: str, params: Dict[str, Any]) -> bool:
        """执行操作"""
        if not self.is_connected():
            raise RuntimeError("WebExecutor not connected")
        logger.info(f"执行操作 action_type={action_type}, params={params}, serial_id={self._serial_id}")
        if action_type == "click":
            selector = params.get("selector")
            elem = self.find_element(By.CSS_SELECTOR, selector)
            if elem:
                elem.click()
                return True
        return False
    
    def get_adb_device(self) -> adbutils.AdbDevice:
        """获取 ADB 设备实例"""
        return self.adb_device

    def __enter__(self):
        """支持上下文管理器"""
        if not self.connect():
            raise RuntimeError(f"Failed to connect device: {self._serial_id}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动断开连接"""
        self.disconnect()