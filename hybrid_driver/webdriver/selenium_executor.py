import logging
import time
import os
from typing import Optional, Any, List, Union

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from hybrid_driver.webdriver.web_executor import WebExecutor
from hybrid_driver.api.models import ConnectConfig, OperationItem
from hybrid_driver.config.settings import settings
from hybrid_driver.log_config import get_logger
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils

logger = get_logger(__name__)

TEST_CONFIG = {
    "chrome_version": "134.0.6998.136",
    "ip": "172.16.1.125",
    "port": 6520,
    "device_serial": "test_serial",
    "android_process": "com.tencent.mm:appbrand0",
    "android_package": "com.tencent.mm"
}


def try_close_popup(driver, timeout=5):
    """
    尝试在页面上关闭弹框。
    1) 等待 timeout 秒，看是否出现带有 "ad-pop-index--close-icon-new" 这个 class 的 close 按钮。
    2) 如果出现，就点击并返回 True；否则返回 False。
    """
    try:
        close_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".ad-pop-index--close-icon-new"))
        )
        close_btn.click()
        return True
    except TimeoutException:
        # 弹框未出现或关闭按钮不可点击
        return False


def get_miniprogram_current_page(driver):
    """
    获取微信小程序 WebView 当前业务页面的路由（如 pages/index/menu）
    :param driver: Selenium WebDriver 实例
    :return: 当前页面路由字符串，获取不到时返回空字符串
    """
    js = """
        try {
            if (window.__wxRoute__) return window.__wxRoute__;
            if (typeof getCurrentPages === 'function') {
                var pages = getCurrentPages();
                if (pages && pages.length) {
                    // 兼容微信原生和部分框架
                    if (pages[pages.length-1].route) {
                        return pages[pages.length-1].route;
                    }
                    if (pages[pages.length-1].__route__) {
                        return pages[pages.length-1].__route__;
                    }
                }
            }
            return '';
        } catch(e) {
            return '';
        }
    """
    return driver.execute_script(js)


def find_chromedriver(path):
    # 如果 path 就是可执行文件且文件名正确，直接返回
    basename = os.path.basename(path)
    logger.info(f"basename: {basename}, path: {path}")
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
    logger.info(f"开始创建 WebDriver serial_id={serial_id}")
    options = ChromeOptions()

    options.enable_mobile(
        android_package=TEST_CONFIG["android_package"],
        device_serial=serial_id,
    )
    options.add_experimental_option("androidUseRunningApp", True)
    options.add_experimental_option("androidProcess", TEST_CONFIG["android_process"])

    options.set_capability("browserName","chrome")

    logger.info(f"Chrome 选项配置: {options.to_capabilities()}")

    if settings.WEBDRIVER_MODE == "remote":
        # 远程 WebDriver
        remote_url = settings.REMOTE_WEBDRIVER_URL
        if not remote_url:
            raise ValueError("REMOTE_WEBDRIVER_URL 未配置")
        logger.info(f"使用 RemoteWebDriver: {remote_url}")
        options.set_capability("browserVersion", "138")
        options.set_capability("platformName", "linux")

        driver = webdriver.Remote(
            command_executor=remote_url,
            options=options
        )
        driver.implicitly_wait(3)
        logger.info(f"RemoteWebDriver 创建成功 serial_id={serial_id}")
        return driver
    else:
        # 本地 WebDriver
        options.set_capability("browserVersion", TEST_CONFIG["chrome_version"])
        options.set_capability("platformName", "android")
        path = ChromeDriverManager(driver_version=TEST_CONFIG["chrome_version"]).install()
        logger.info(f"ChromeDriver 路径: {path}")
        if 'THIRD_PARTY_NOTICES.chromedriver' in path:
            path = path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
            logger.info(f"更新后的 ChromeDriver 路径: {path}")
        service = ChromeService(executable_path=path)
        driver = webdriver.Chrome(options=options, service=service)
        driver.implicitly_wait(3)
        logger.info(f"WebDriver 创建成功 serial_id={serial_id}")
        return driver


def connect_webdriver_with_config(config: ConnectConfig) -> WebDriver:
    """使用 ConnectConfig 创建 WebDriver"""
    # 确保 config 是 ConnectConfig 实例
    if not isinstance(config, ConnectConfig):
        logger.error(f"config 不是 ConnectConfig 实例，而是 {type(config)}: {config}")
        raise ValueError(f"Expected ConnectConfig instance, got {type(config)}")
    
    try:
        config_dict = config.model_dump()
        logger.info(f"开始创建 WebDriver config={config_dict}")
    except AttributeError as e:
        logger.error(f"config 对象没有 model_dump 方法: {e}")
        # 尝试使用 dict() 方法作为备选
        try:
            config_dict = dict(config)
            logger.info(f"使用 dict() 方法获取配置: {config_dict}")
        except Exception as e2:
            logger.error(f"无法获取配置信息: {e2}")
            config_dict = {"serial_id": str(config)}
            logger.info(f"使用默认配置: {config_dict}")
    options = ChromeOptions()

    # 使用配置中的参数
    options.enable_mobile(
        android_package=config.android_package,
        device_serial=config.serial_id,
    )
    options.add_experimental_option("androidUseRunningApp", True)
    if config.android_process:
        options.add_experimental_option("androidProcess", config.android_process)

    options.set_capability("browserName", "chrome")
    
    # 设置浏览器版本和平台
    if config.browser_version:
        options.set_capability("browserVersion", config.browser_version)

    options.set_capability("platformName", "linux")

    logger.info(f"Chrome 选项配置: {options.to_capabilities()}")

    if config.webdriver_mode == "remote":
        # 远程 WebDriver
        remote_url = config.remote_url or settings.REMOTE_WEBDRIVER_URL
        if not remote_url:
            raise ValueError("REMOTE_WEBDRIVER_URL 未配置")
        logger.info(f"使用 RemoteWebDriver: {remote_url}")

        driver = webdriver.Remote(
            command_executor=remote_url,
            options=options
        )
        driver.implicitly_wait(3)
        logger.info(f"RemoteWebDriver 创建成功 serial_id={config.serial_id}")
        return driver
    else:
        # 本地 WebDriver
        path = ChromeDriverManager(driver_version=config.browser_version or TEST_CONFIG["chrome_version"]).install()
        logger.info(f"ChromeDriver 路径: {path}")
        if 'THIRD_PARTY_NOTICES.chromedriver' in path:
            path = path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
            logger.info(f"更新后的 ChromeDriver 路径: {path}")
        service = ChromeService(executable_path=path)
        driver = webdriver.Chrome(options=options, service=service)
        driver.implicitly_wait(3)
        logger.info(f"WebDriver 创建成功 serial_id={config.serial_id}")
        return driver


class SeleniumWebExecutor(WebExecutor):
    """Selenium WebDriver 实现"""

    def __init__(self):
        self._driver: WebDriver = None
        self._device_id = None
        logger.info("初始化完成")

    def connect(self, device_id_or_config: Union[str, ConnectConfig], **kwargs) -> bool:
        """
        连接到设备
        :param device_id_or_config: 设备序列号或连接配置
        :param kwargs: 其他参数
        :return: 是否连接成功
        """
        try:
            if isinstance(device_id_or_config, ConnectConfig):
                # 使用 ConnectConfig
                config = device_id_or_config
                self._driver = connect_webdriver_with_config(config)
                self._device_id = config.serial_id
                logger.info(f"设备连接成功 serial_id={config.serial_id}")
            else:
                # 向后兼容：使用字符串
                serial_id = device_id_or_config
                self._driver = connect_webdriver(serial_id)
                self._device_id = serial_id
                logger.info(f"设备连接成功 serial_id={serial_id}")
            return True
        except Exception as e:
            logger.error(f"设备连接失败: {e}")
            return False

    def quit(self) -> None:
        """
        断开连接
        """
        try:
            if self._driver:
                self._driver.quit()
                self._driver = None
                self._device_id = None
                logger.info("WebDriver 资源已清理")
        except Exception as e:
            logger.error(f"断开连接失败: {e}")

    def is_alive(self) -> bool:
        """
        检查连接是否存活
        :return: 是否存活
        """
        try:
            return self._driver is not None
        except:
            return False

    def find_element(self, by: str, value: str) -> Optional[WebElement]:
        """
        查找元素
        :param by: 定位方式
        :param value: 定位值
        :return: 元素对象
        """
        try:
            if self._driver is None:
                logger.error("WebDriver未初始化")
                return None
            return self._driver.find_element(by, value)
        except Exception as e:
            logger.error(f"查找元素失败: {e}")
            return None

    def find_elements(self, by: str, value: str) -> Optional[List[WebElement]]:
        """
        查找多个元素
        :param by: 定位方式
        :param value: 定位值
        :return: 元素列表
        """
        try:
            if self._driver is None:
                logger.error("WebDriver未初始化")
                return None
            return self._driver.find_elements(by, value)
        except Exception as e:
            logger.error(f"查找元素失败: {e}")
            return None

    def wait_for_element(self, by: str, value: str, timeout: int = 10, trace_id: str = None) -> Optional[WebElement]:
        """
        等待元素出现
        :param by: 定位方式
        :param value: 定位值
        :param timeout: 超时时间
        :param trace_id: 追踪ID
        :return: 元素对象
        """
        if self._driver is None:
            logger.error("WebDriver未初始化")
            return None
        return WebDriverUtils.wait_for_element(self._driver, by, value, timeout, trace_id)

    def wait_for_new_window(self, timeout: int = 10, old_handles: Optional[set] = None) -> Optional[str]:
        """
        等待新窗口出现
        :param timeout: 超时时间
        :param old_handles: 旧窗口句柄集合
        :return: 新窗口句柄
        """
        if self._driver is None:
            logger.error("WebDriver未初始化")
            return None
        return WebDriverUtils.wait_for_new_window(self._driver, timeout, old_handles)

    def wait_for_page_load(self, timeout: int = 10) -> bool:
        """
        等待页面加载完成
        :param timeout: 超时时间
        :return: 是否加载完成
        """
        if self._driver is None:
            logger.error("WebDriver未初始化")
            return False
        return WebDriverUtils.wait_for_page_load(self._driver, timeout)

    def execute_script(self, script: str, *args) -> Any:
        """
        执行JavaScript脚本
        :param script: 脚本内容
        :param args: 脚本参数
        :return: 执行结果
        """
        try:
            if self._driver is None:
                logger.error("WebDriver未初始化")
                return None
            return self._driver.execute_script(script, *args)
        except Exception as e:
            logger.error(f"执行脚本失败: {e}")
            return None

    def get_current_url(self) -> str:
        """
        获取当前URL
        :return: URL字符串
        """
        try:
            if self._driver is None:
                logger.error("WebDriver未初始化")
                return ""
            return self._driver.current_url
        except Exception as e:
            logger.error(f"获取URL失败: {e}")
            return ""

    def get_page_source(self) -> str:
        """
        获取页面源码
        :return: 页面源码字符串
        """
        try:
            if self._driver is None:
                logger.error("WebDriver未初始化")
                return ""
            return self._driver.page_source
        except Exception as e:
            logger.error(f"获取页面源码失败: {e}")
            return ""

    def handle_common_popups(self) -> None:
        """
        处理常见弹窗
        """
        try:
            if self._driver is None:
                logger.error("WebDriver未初始化")
                return
                
            popup_selectors = [
                "button.close",
                ".modal-close",
                ".popup-close",
                "#cookie-consent button",
                ".cookie-banner button"
            ]

            logger.info(f"开始查找弹窗选择器: {popup_selectors}")
            for selector in popup_selectors:
                try:
                    # 使用find_element而不是wait_for_element，避免不必要的等待
                    element = self._driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        element.click()
                        logger.info(f"关闭弹窗: {selector}")
                except NoSuchElementException:
                    # 元素不存在，继续检查下一个
                    continue
                except Exception as e:
                    logger.warning(f"处理弹窗异常: {selector}, error={e}")
                    continue
        except Exception as e:
            logger.error(f"处理弹窗失败: {e}")

    def get_window_handles(self) -> list:
        """
        获取所有窗口句柄
        :return: 窗口句柄列表
        """
        try:
            if self._driver is None:
                logger.error("WebDriver未初始化")
                return []
            return self._driver.window_handles
        except Exception as e:
            logger.error(f"获取窗口句柄失败: {e}")
            return []

    def switch_to_window(self, handle: str) -> None:
        """
        切换到指定窗口
        :param handle: 窗口句柄
        """
        try:
            if self._driver is None:
                logger.error("WebDriver未初始化")
                return
            self._driver.switch_to.window(handle)
        except Exception as e:
            logger.error(f"切换窗口失败: {e}")

    def switch_to_new_window(self) -> None:
        try:
            if self._driver is None:
                logger.error("WebDriver未初始化")
                return
            visible_page = WebDriverUtils.get_visible_page(self._driver)
            self.switch_to_window(visible_page[0].handle)
            logger.info(f"切换到当前可见的 page: {visible_page[0]}")
        except Exception as e:
            logger.error(f"切换到新窗口失败: {e}")

    def get_current_window_handle(self) -> str:
        """
        获取当前窗口句柄
        :return: 窗口句柄
        """
        try:
            if self._driver is None:
                logger.error("WebDriver未初始化")
                return ""
            return self._driver.current_window_handle
        except Exception as e:
            logger.error(f"获取当前窗口句柄失败: {e}")
            return ""

    def get_visible_pages(self, timeout: int = 10) -> list[Any] | str:
        """获取可见页面列表"""
        if self._driver is None:
            logger.error("WebDriver未初始化")
            return []
        return WebDriverUtils.get_visible_page(self._driver, 10)

    def get_raw_remote_webdriver(self) -> Optional[selenium.webdriver.remote.webdriver.WebDriver]:
        """获取原始WebDriver实例"""
        return self._driver

"""
search btn:


"""


def main():
    from hybrid_driver.device_pool import DevicePool

    config = ConnectConfig(
        serial_id="47.94.130.125:6521",
        user_id="0",
        android_process="com.tencent.mm:appbrand0"
    )
    device = DevicePool().connect(config)

    # switch to current page
    driver = device._web_execute._driver

    pages = WebDriverUtils.get_visible_page(driver)
    try:
        # 构建操作序列
        operations = [
            # # click menu
            # OperationItem("click",
            #               native_action="ACTION_CLICK --close_dialog=1 --pkg=com.tencent.mm --id=com.tencent.mm:id/a0g --text=菜单",
            #               context_type="NATIVE", wait_for_new_window=True),
            # # 查找搜索按钮
            # OperationItem("find", method="css selector", selector="wx-view.query.menu-bar--query", timeout=2),
            # # 点击搜索按钮并等待新窗口
            # OperationItem("click", wait_for_new_window=True, timeout=2),
            # # 等待新页面渲染
            # OperationItem("wait_for_page_render", timeout=1),
            # # 查找输入框
            # OperationItem("find", method="css selector",
            #               selector="wx-input.query-bar--input_native[confirm-type='search']", timeout=2),
            # OperationItem("click", wait_for_new_window=False, timeout=2),
            # # 输入搜索文本
            OperationItem("input_text", text="拿铁"),
            # # 查找搜索按钮
            # OperationItem("find", method="css selector", selector="wx-view.btn_query.query-bar--btn_query",
            #               timeout=2),
            # # 点击搜索按钮
            # OperationItem("click")
        ]

        # 构建并执行操作序列
        sequence = OperationSequence(operations)
        results = sequence.execute(device)

        # 打印结果
        for i, result in enumerate(results):
            print(f"Step {i + 1}: {'Success' if result['success'] else 'Failed'}")
            if not result['success']:
                print(f"Error: {result['error']}")
            print(f"Time: {result['elapsed']:.2f}s")
    except Exception as e:
        logger.error(f"执行操作序列失败: {e}")
    finally:
        driver.quit()

def lucky_login():

    operations = [
        OperationItem("click", wait_for_new_window=True, timeout=2),
    ]

def connect_remote_local():
    serial_id = "172.16.1.125:6569"
    logger.info(f"开始创建 WebDriver serial_id={serial_id}")
    options = ChromeOptions()

    options.enable_mobile(
        android_package="mark.via",
        device_serial=serial_id,
    )
    options.add_experimental_option("androidUseRunningApp", True)
    options.add_experimental_option("androidProcess", "mark.via")
    options.add_experimental_option("mobileProcess", "mark.via")

    # capabilities = options.to_capabilities()

    # capabilities["browserVersion"] = "128.0.6613.88"

    logger.info(f"Chrome 选项配置: {options.to_capabilities()}")

    remote_url = "http://172.16.1.129:4444/wd/hub"
    if not remote_url:
        raise ValueError("REMOTE_WEBDRIVER_URL 未配置")
    logger.info(f"使用 RemoteWebDriver: {remote_url}")
    driver = webdriver.Remote(
        command_executor=remote_url,
        options=options
    )
    driver.implicitly_wait(3)
    logger.info(f"RemoteWebDriver 创建成功 serial_id={serial_id}")

    logger.info(f"page : {driver.page_source}")

def connect_remote():
    serial_id = "172.16.1.125:6569"
    logger.info(f"开始创建 WebDriver serial_id={serial_id}")
    options = ChromeOptions()

    # # WebView专用配置
    options.enable_mobile(
        android_package="com.tencent.mm",
        device_serial=serial_id,
        android_activity="com.tencent.mm"
    )
    #
    # 添加WebView专用选项
    options.add_experimental_option("androidUseRunningApp", True)
    options.add_experimental_option('androidDeviceSerial', serial_id)
    options.add_experimental_option("androidProcess", "com.tencent.mm:appbrand0")
    options.set_capability("browserVersion", "138")
    options.set_capability("platformName", "linux")
    options.set_capability("browserName","chrome")
    # options.set_capability("se:serial_id", serial_id)
    options.set_capability("se:adbDeviceId", serial_id)

    logger.info(f"Chrome 选项配置: {options.to_capabilities()}")

    # 连接到WebView节点
    remote_url = "http://172.16.1.129:4444/wd/hub"
    if not remote_url:
        raise ValueError("REMOTE_WEBDRIVER_URL 未配置")
    
    logger.info(f"使用 RemoteWebDriver: {remote_url}")
    # options.debugger_address = "localhost:9222"
    
    try:
        driver = webdriver.Remote(
            command_executor=remote_url,
            options=options
        )
        driver.implicitly_wait(3)
        logger.info(f"RemoteWebDriver 创建成功 serial_id={serial_id}")
        
        # 获取页面信息
        current_url = driver.current_url
        logger.info(f"当前页面URL: {current_url}")

        # 获取页面源码（限制长度避免日志过长）
        page_source = driver.page_source
        if len(page_source) > 500:
            logger.info(f"页面源码预览: {page_source[:500]}...")
        else:
            logger.info(f"页面源码: {page_source}")

        for window_handle in driver.window_handles:
            driver.switch_to.window(window_handle)
            logger.info(f"<title>: {driver.title}")
            
        return driver
        
    except Exception as e:
        logger.error(f"RemoteWebDriver 创建失败: {e}")
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    # main()
    connect_remote()
