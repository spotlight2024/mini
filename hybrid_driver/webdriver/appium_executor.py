import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from hybrid_driver.webdriver.web_executor import WebExecutor
from selenium.webdriver.remote.webelement import WebElement
from typing import Optional, Any, List

class AppiumExecutor(WebExecutor):
    def __init__(self, appium_server_url=None, capabilities=None):
        self.driver = None
        self._appium_server_url = appium_server_url
        self._capabilities = capabilities or {}

    def connect(self, device_id: str, **kwargs) -> bool:
        from appium import webdriver
        from appium.options.android import UiAutomator2Options
        options = UiAutomator2Options()
        for k, v in self._capabilities.items():
            options.set_capability(k, v)
        options.set_capability('deviceName', device_id)
        self.driver = webdriver.Remote(
            command_executor=self._appium_server_url,
            options=options
        )
        return True

    def quit(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None

    def is_alive(self) -> bool:
        return self.driver is not None

    def find_element(self, by: str, value: str) -> Optional[WebElement]:
        try:
            return self.driver.find_element(by, value)
        except Exception:
            return None

    def find_elements(self, by: str, value: str) -> Optional[List[WebElement]]:
        try:
            return self.driver.find_elements(by, value)
        except Exception:
            return None

    def wait_for_element(self, by: str, value: str, timeout: int = 10) -> Optional[WebElement]:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except Exception:
            return None

    def execute_script(self, script: str, *args) -> Any:
        try:
            return self.driver.execute_script(script, *args)
        except Exception:
            return None

    def get_current_url(self) -> str:
        try:
            return self.driver.current_url
        except Exception:
            return ""

    def get_page_source(self) -> str:
        try:
            return self.driver.page_source
        except Exception:
            return ""

    def handle_common_popups(self) -> None:
        # 可根据实际业务实现
        pass

    def get_window_handles(self) -> list:
        try:
            return self.driver.window_handles
        except Exception:
            return []

    def switch_to_window(self, handle: str) -> None:
        try:
            self.driver.switch_to.window(handle)
        except Exception:
            pass

    def get_current_window_handle(self) -> str:
        try:
            return self.driver.current_window_handle
        except Exception:
            return ""

    def switch_to_new_window(self) -> None:
        # 可根据实际业务实现
        pass

    def get_visible_pages(self, timeout: int = 10) -> list:
        """获取可见页面列表（Appium场景下可自定义扩展）"""
        if self.driver is None:
            return []
        # Appium场景下暂时返回所有window_handles
        try:
            return self.driver.window_handles
        except Exception:
            return []

if __name__ == "__main__":
    # 这些是您希望在哪个节点上运行测试的“要求”。
    # Selenium Grid 会将这些要求与注册上来节点（在 appium-node.toml 中定义）的
    # 能力(stereotype)进行匹配。
    capabilities = {
        "platformName": "Android",
        # 以下为 Appium 特有的 capabilities，推荐使用 'appium:' 前缀
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": "172.16.1.125:6556",
        "appium:appPackage": "com.tencent.mm",
        "appium:appActivity": "com.tencent.mm/.plugin.appbrand.ui.AppBrandUI00",
        "appium:noReset": True,
        "appium:unicodeKeyboard": True,
        "appium:resetKeyboard": True,
        "appium:autoGrantPermissions": True,
        "appium:chromeOptions": {
            "androidProcess": "com.tencent.mm:appbrand0"
        }
        # 不再需要硬编码 chromedriver 的路径
        # "chromedriverExecutable": "..."
    }

    # 将 command_executor 指向 Selenium Grid Hub 的地址
    # 您的所有请求都将发送到这里，由 Hub 负责分发
    appium_server_url = "http://localhost:4444"

    executor = AppiumExecutor(appium_server_url, capabilities)
    try:
        # executor.wait_for_context('WEBVIEW')
        # executor.input_text(By.CSS_SELECTOR, 'input[type=\"text\"]', '拿铁')
        executor.test()
    finally:
        executor.quit()