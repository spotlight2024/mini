import logging
import uuid
from dataclasses import dataclass
from typing import Optional, Any, List, Dict
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from log_config import get_logger
from operation import FindElement, build_operations, OperationSequence, OperationItem
from webdriver.popup_handler import PopupHandler
from webdriver.web_executor import WebExecutor
from webdriver.webdriver_utils import WebDriverUtils

import os

# 获取logger实例
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
    options = webdriver.ChromeOptions()

    options.enable_mobile(
        android_package=TEST_CONFIG["android_package"],
        device_serial=serial_id,
    )
    options.add_experimental_option("androidUseRunningApp", True)
    options.add_experimental_option("androidProcess", TEST_CONFIG["android_process"])

    logger.info(f"Chrome 选项配置: {options.to_capabilities()}")

    path = ChromeDriverManager(driver_version=TEST_CONFIG["chrome_version"]).install()
    logger.info(f"ChromeDriver 路径: {path}")

    # 新版本chromedriver的文件名是THIRD_PARTY_NOTICES.chromedriver，需要替换为chromedriver
    if 'THIRD_PARTY_NOTICES.chromedriver' in path:
        path = path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
        logger.info(f"更新后的 ChromeDriver 路径: {path}")

    service = Service(executable_path=path)
    driver = webdriver.Chrome(options=options, service=service)
    driver.implicitly_wait(3)
    logger.info(f"WebDriver 创建成功 serial_id={serial_id}")

    return driver


class SeleniumWebExecutor(WebExecutor):
    """Selenium WebDriver 实现"""

    def __init__(self):
        self._driver = None
        self._device_id = None
        logger.info("初始化完成")

    def connect(self, serial_id: str, **kwargs) -> bool:
        """
        连接到设备
        :param serial_id: 设备序列号
        :param kwargs: 其他参数
        :return: 是否连接成功
        """
        try:
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
        return WebDriverUtils.wait_for_element(self._driver, by, value, timeout, trace_id)

    def wait_for_new_window(self, timeout: int = 10, old_handles: Optional[set] = None) -> Optional[str]:
        """
        等待新窗口出现
        :param timeout: 超时时间
        :param old_handles: 旧窗口句柄集合
        :return: 新窗口句柄
        """
        return WebDriverUtils.wait_for_new_window(self._driver, timeout, old_handles)

    def wait_for_page_load(self, timeout: int = 10) -> bool:
        """
        等待页面加载完成
        :param timeout: 超时时间
        :return: 是否加载完成
        """
        return WebDriverUtils.wait_for_page_load(self._driver, timeout)

    def execute_script(self, script: str, *args) -> Any:
        """
        执行JavaScript脚本
        :param script: 脚本内容
        :param args: 脚本参数
        :return: 执行结果
        """
        try:
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
            return self._driver.page_source
        except Exception as e:
            logger.error(f"获取页面源码失败: {e}")
            return ""

    def handle_common_popups(self) -> None:
        """
        处理常见弹窗
        """
        try:
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
            self._driver.switch_to.window(handle)
        except Exception as e:
            logger.error(f"切换窗口失败: {e}")

    def switch_to_new_window(self) -> None:
        try:
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
            return self._driver.current_window_handle
        except Exception as e:
            logger.error(f"获取当前窗口句柄失败: {e}")
            return ""


"""
search btn:


"""


def main():
    try:
        from device_pool import DevicePool

        # 连接设备
        device = DevicePool().connect("JJGICIN7QOAELNGI")

        # switch to current page
        driver = device._web_execute._driver

        pages = WebDriverUtils.get_visible_page(driver)
        driver.switch_to.window(pages[0].handle)

        try:
            # 构建操作序列
            operations = [
                # 查找搜索按钮
                OperationItem("find", method="css selector", selector="wx-view.query.menu-bar--query", timeout=2),
                # 点击搜索按钮并等待新窗口
                OperationItem("click", wait_for_new_window=True, timeout=2),
                # 等待新页面渲染
                OperationItem("wait_for_page_render", timeout=1),
                # 查找输入框
                OperationItem("find", method="css selector",
                              selector="wx-input.query-bar--input_native[confirm-type='search']", timeout=2,wait_for_new_window=False),
                OperationItem("click", wait_for_new_window=False, timeout=2),
                # # 输入搜索文本
                OperationItem("input_text", text="拿铁"),
                # 查找搜索按钮
                OperationItem("find", method="css selector", selector="wx-view.btn_query.query-bar--btn_query", timeout=2),
                # 点击搜索按钮
                OperationItem("click")
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

    finally:
        # 断开设备连接
        device.disconnect()


if __name__ == "__main__":
    main()
