import logging
from typing import Optional, Any

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from log_config import setup_logging
from .popup_handler import PopupHandler
from .web_executor import WebExecutor

import os

setup_logging()

TEST_CONFIG = {
    "chrome_version": "134.0.6998.136",
    "ip": "172.16.1.125",
    "port": 6520,
    "device_serial": "test_serial",
    "android_process": "com.tencent.mm:appbrand0",
    "android_package": "com.tencent.mm"
}


def find_chromedriver(path):
    # 如果 path 就是可执行文件且文件名正确，直接返回
    basename = os.path.basename(path)
    logging.info(f"basename: {basename}, path: {path}")
    if (basename in ("chromedriver", "chromedriver-mac-arm64")) and os.path.isfile(path) and os.access(path,
                                                                                                       os.X_OK):
        return path
    # 否则在目录下查找
    for root, dirs, files in os.walk(path):
        for file in files:
            # 只认精确文件名，且排除任何包含 'THIRD_PARTY' 的文件
            if file in ("chromedriver", "chromedriver-mac-arm64") and "THIRD_PARTY" not in file:
                full_path = os.path.join(root, file)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    return full_path
    raise FileNotFoundError("No valid chromedriver executable found.")


def connect_webdriver(serial_id: str) -> WebDriver:
    logging.info(f"[SeleniumWebExecutor] 开始创建 WebDriver serial_id={serial_id}")
    options = webdriver.ChromeOptions()

    options.enable_mobile(
        android_package=TEST_CONFIG["android_package"],
        device_serial=serial_id,
    )
    options.add_experimental_option("androidUseRunningApp", True)
    options.add_experimental_option("androidProcess", TEST_CONFIG["android_process"])

    logging.info(f"[SeleniumWebExecutor] Chrome 选项配置: {options.to_capabilities()}")

    path = ChromeDriverManager(driver_version=TEST_CONFIG["chrome_version"]).install()
    logging.info(f"[SeleniumWebExecutor] ChromeDriver 路径: {path}")

    # 新版本chromedriver的文件名是THIRD_PARTY_NOTICES.chromedriver，需要替换为chromedriver
    if 'THIRD_PARTY_NOTICES.chromedriver' in path:
        path = path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
        logging.info(f"[SeleniumWebExecutor] 更新后的 ChromeDriver 路径: {path}")

    service = Service(executable_path=path)
    driver = webdriver.Chrome(options=options, service=service)
    driver.implicitly_wait(3)
    logging.info(f"[SeleniumWebExecutor] WebDriver 创建成功 serial_id={serial_id}")

    return driver


class SeleniumWebExecutor(WebExecutor):
    """Selenium WebDriver 实现"""

    def __init__(self):
        self._driver: Optional[webdriver.Chrome] = None
        self._device_id: Optional[str] = None
        self._popup_handler = PopupHandler()
        logging.info("[SeleniumWebExecutor] 初始化完成")

    def connect(self, serial_id: str, **kwargs) -> bool:
        """连接设备"""
        try:
            logging.info(f"[SeleniumWebExecutor] 开始连接设备 serial_id={serial_id}")
            self._driver = connect_webdriver(serial_id)
            self._device_id = serial_id
            logging.info(f"[SeleniumWebExecutor] 设备连接成功 serial_id={serial_id}")
            return True
        except WebDriverException as e:
            logging.error(f"[SeleniumWebExecutor] 设备连接失败 serial_id={serial_id}: {e}")
            return False

    def quit(self) -> None:
        """关闭连接"""
        if self._driver:
            try:
                logging.info(f"[SeleniumWebExecutor] 开始关闭 WebDriver device_id={self._device_id}")
                self._driver.quit()
                logging.info(f"[SeleniumWebExecutor] WebDriver 关闭成功 device_id={self._device_id}")
            except Exception as e:
                logging.error(f"[SeleniumWebExecutor] WebDriver 关闭失败 device_id={self._device_id}: {e}")
            finally:
                self._driver = None
                self._device_id = None
                logging.info(f"[SeleniumWebExecutor] WebDriver 资源已清理")

    def is_alive(self) -> bool:
        """检查连接是否存活"""
        if not self._driver:
            logging.debug("[SeleniumWebExecutor] WebDriver 未初始化")
            return False
        try:
            self._driver.current_url
            logging.debug(f"[SeleniumWebExecutor] WebDriver 状态正常 device_id={self._device_id}")
            return True
        except:
            logging.warning(f"[SeleniumWebExecutor] WebDriver 已断开连接 device_id={self._device_id}")
            return False

    def find_element(self, by: str, value: str) -> Optional[WebElement]:
        """查找元素"""
        if not self._driver:
            logging.warning("[SeleniumWebExecutor] 查找元素失败: WebDriver 未初始化")
            return None
        try:
            element = self._driver.find_element(by, value)
            logging.debug(f"[SeleniumWebExecutor] 元素查找成功 by={by}, value={value}")
            return element
        except NoSuchElementException:
            logging.warning(f"[SeleniumWebExecutor] 未找到元素 by={by}, value={value}")
            return None

    def wait_for_element(self, by: str, value: str, timeout: int = 10) -> Optional[WebElement]:
        """等待元素出现"""
        if not self._driver:
            logging.warning(f"[SeleniumWebExecutor] 等待元素失败: WebDriver 未初始化, device_id={self._device_id}")
            return None
        try:
            logging.info(f"[SeleniumWebExecutor] 开始等待元素 by={by}, value={value}, timeout={timeout}, device_id={self._device_id}")
            element = WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            logging.info(f"[SeleniumWebExecutor] 元素等待成功 by={by}, value={value}, device_id={self._device_id}")
            return element
        except TimeoutException:
            logging.warning(f"[SeleniumWebExecutor] 元素等待超时 by={by}, value={value}, timeout={timeout}, device_id={self._device_id}")
            return None

    def execute_script(self, script: str, *args) -> Any:
        """执行 JavaScript"""
        if not self._driver:
            logging.warning("[SeleniumWebExecutor] 执行脚本失败: WebDriver 未初始化")
            return None
        try:
            result = self._driver.execute_script(script, *args)
            logging.debug(f"[SeleniumWebExecutor] 脚本执行成功 script={script}")
            return result
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 脚本执行失败 script={script}: {e}")
            return None

    def get_current_url(self) -> str:
        """获取当前 URL"""
        if not self._driver:
            logging.warning("[SeleniumWebExecutor] 获取 URL 失败: WebDriver 未初始化")
            return ""
        try:
            url = self._driver.current_url
            logging.debug(f"[SeleniumWebExecutor] 当前 URL: {url}")
            return url
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 获取 URL 失败: {e}")
            return ""

    def get_page_source(self) -> str:
        """获取页面源码"""
        if not self._driver:
            logging.warning("[SeleniumWebExecutor] 获取页面源码失败: WebDriver 未初始化")
            return ""
        try:
            source = self._driver.page_source
            logging.debug("[SeleniumWebExecutor] 页面源码获取成功")
            return source
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 获取页面源码失败: {e}")
            return ""

    def handle_common_popups(self) -> None:
        """处理常见弹窗"""
        if not self._driver:
            logging.warning("[SeleniumWebExecutor] 处理弹窗失败: WebDriver 未初始化")
            return
        try:
            logging.info("[SeleniumWebExecutor] 开始处理弹窗")
            self._popup_handler.handle_popups(self._driver)
            logging.info("[SeleniumWebExecutor] 弹窗处理完成")
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 处理弹窗失败: {e}")

    def get_window_handles(self) -> list:
        """获取所有窗口句柄"""
        if not self._driver:
            logging.warning("[SeleniumWebExecutor] 获取窗口句柄失败: WebDriver 未初始化")
            return []
        try:
            handles = self._driver.window_handles
            logging.debug(f"[SeleniumWebExecutor] 获取到 {len(handles)} 个窗口句柄")
            return handles
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 获取窗口句柄失败: {e}")
            return []

    def switch_to_window(self, handle: str) -> None:
        """切换到指定窗口"""
        if not self._driver:
            logging.warning("[SeleniumWebExecutor] 切换窗口失败: WebDriver 未初始化")
            return
        try:
            logging.info(f"[SeleniumWebExecutor] 开始切换到窗口 handle={handle}")
            self._driver.switch_to.window(handle)
            logging.info(f"[SeleniumWebExecutor] 窗口切换成功 handle={handle}")
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 切换窗口失败 handle={handle}: {e}")

    def get_current_window_handle(self) -> str:
        """获取当前窗口句柄"""
        if not self._driver:
            logging.warning("[SeleniumWebExecutor] 获取当前窗口句柄失败: WebDriver 未初始化")
            return ""
        try:
            handle = self._driver.current_window_handle
            logging.debug(f"[SeleniumWebExecutor] 当前窗口句柄: {handle}")
            return handle
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 获取当前窗口句柄失败: {e}")
            return ""
