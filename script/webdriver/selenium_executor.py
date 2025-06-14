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

from operation import FindElement, build_operations, OperationSequence, OperationItem
from webdriver.popup_handler import PopupHandler
from webdriver.web_executor import WebExecutor
from webdriver.webdriver_utils import WebDriverUtils

import os

from log_config import setup_logging

setup_logging()

TEST_CONFIG = {
    "chrome_version": "134.0.6998.136",
    "ip": "172.16.1.125",
    "port": 6520,
    "device_serial": "test_serial",
    "android_process": "com.tencent.mm:appbrand0",
    "android_package": "com.tencent.mm"
}


@dataclass
class Page:
    """页面信息类"""
    handle: str
    url: str
    title: str
    is_visible: bool
    is_foreground: bool
    viewport_width: int
    viewport_height: int
    is_active: bool
    is_hidden: bool
    state: Dict[str, Any]

    @property
    def is_actually_visible(self) -> bool:
        """判断页面是否真正可见"""
        return (
                self.is_visible and
                not self.is_hidden and
                self.viewport_width > 0 and
                self.viewport_height > 0
        )


class PageVisibilityCondition:
    """页面可见性条件类"""

    def __init__(self, min_visible_pages: int = 1):
        self.min_visible_pages = min_visible_pages

    def __call__(self, driver: WebDriver) -> List[Page]:
        """
        检查页面可见性条件

        Args:
            driver: WebDriver 实例

        Returns:
            List[Page]: 如果条件满足返回可见页面列表，否则返回 False
        """
        visible_pages = get_visible_page(driver)
        if len(visible_pages) >= self.min_visible_pages:
            return visible_pages
        return False


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


def get_visible_page(driver: WebDriver) -> List[Page]:
    """
    获取所有可见页面的信息

    Args:
        driver: WebDriver 实例

    Returns:
        List[Page]: 可见页面列表
    """
    visible_pages = []

    for handle in driver.window_handles:
        driver.switch_to.window(handle)

        current_url = driver.current_url
        current_title = driver.title

        # 获取页面状态
        page_state = driver.execute_script("""
            return {
                visibilityState: document.visibilityState,
                hidden: document.hidden,
                displayState: document.webkitVisibilityState,
                isActive: document.hasFocus(),
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
                scrollX: window.scrollX,
                scrollY: window.scrollY
            }
        """)

        logging.info(f"page_state : {page_state}")

        # 创建页面对象
        page = Page(
            handle=handle,
            url=current_url,
            title=current_title,
            is_visible=page_state['visibilityState'] == 'visible',
            is_foreground=False,  # 将在下面更新
            viewport_width=page_state['viewportWidth'],
            viewport_height=page_state['viewportHeight'],
            is_active=page_state['isActive'],
            is_hidden=page_state['hidden'],
            state=page_state
        )

        # 检查页面是否在前台
        try:
            is_foreground = driver.execute_script("""
                return window.performance && 
                       window.performance.now() && 
                       document.hasFocus() &&
                       !document.hidden;
            """)
            page.is_foreground = is_foreground

            # 记录页面信息
            logging.info(
                f"窗口状态 - Handle: {page.handle} | "
                f"URL: {page.url} | "
                f"Title: {page.title} | "
                f"可见性: {page.is_actually_visible} | "
                f"视口大小: {page.viewport_width}x{page.viewport_height} | "
                f"焦点状态: {page.is_active} | "
                f"隐藏状态: {page.is_hidden}"
            )

            if page.is_foreground:
                logging.info(f"前台页面 - Handle: {page.handle} | URL: {page.url} | title: {page.title}")

        except Exception as e:
            logging.error(f"检查页面状态时出错: {str(e)}")
            continue

        # if page.is_actually_visible or ":VISIBLE" in current_title:
        """
        @TODO 可见页面判断逻辑需要优化，目前为了调试先按简单方案
        """
        if ":VISIBLE" in current_title:
            visible_pages.append(page)

    # 输出可见页面统计
    if visible_pages:
        logging.info(f"可见页面统计 - 总数: {len(visible_pages)}")
        for page in visible_pages:
            logging.info(f"可见页面 - URL: {page.url}")

    return visible_pages


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
        self._driver = None
        self._device_id = None
        logging.info("[SeleniumWebExecutor] 初始化完成")

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
            logging.info(f"[SeleniumWebExecutor] 设备连接成功 serial_id={serial_id}")
            return True
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 设备连接失败: {e}")
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
                logging.info(f"[SeleniumWebExecutor] WebDriver 资源已清理")
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 断开连接失败: {e}")

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
            logging.error(f"[SeleniumWebExecutor] 查找元素失败: {e}")
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
            logging.error(f"[SeleniumWebExecutor] 查找元素失败: {e}")
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
            logging.error(f"[SeleniumWebExecutor] 执行脚本失败: {e}")
            return None

    def get_current_url(self) -> str:
        """
        获取当前URL
        :return: URL字符串
        """
        try:
            return self._driver.current_url
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 获取URL失败: {e}")
            return ""

    def get_page_source(self) -> str:
        """
        获取页面源码
        :return: 页面源码字符串
        """
        try:
            return self._driver.page_source
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 获取页面源码失败: {e}")
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

            logging.info(f"[SeleniumWebExecutor] start find dialog popup selectors: {popup_selectors}")
            for selector in popup_selectors:
                try:
                    # 使用find_element而不是wait_for_element，避免不必要的等待
                    element = self._driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        element.click()
                        logging.info(f"[SeleniumWebExecutor] 关闭弹窗: {selector}")
                except NoSuchElementException:
                    # 元素不存在，继续检查下一个
                    continue
                except Exception as e:
                    logging.warning(f"[SeleniumWebExecutor] 处理弹窗异常: {selector}, error={e}")
                    continue
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 处理弹窗失败: {e}")

    def get_window_handles(self) -> list:
        """
        获取所有窗口句柄
        :return: 窗口句柄列表
        """
        try:
            return self._driver.window_handles
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 获取窗口句柄失败: {e}")
            return []

    def switch_to_window(self, handle: str) -> None:
        """
        切换到指定窗口
        :param handle: 窗口句柄
        """
        try:
            self._driver.switch_to.window(handle)
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 切换窗口失败: {e}")

    def get_current_window_handle(self) -> str:
        """
        获取当前窗口句柄
        :return: 窗口句柄
        """
        try:
            return self._driver.current_window_handle
        except Exception as e:
            logging.error(f"[SeleniumWebExecutor] 获取当前窗口句柄失败: {e}")
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
        selenium_executor: SeleniumWebExecutor = device._web_execute
        wait = WebDriverWait(selenium_executor._driver, 3)  # 最长等待 10 秒
        # 等待页面加载完成并获取可见页面
        visible_pages = wait.until(PageVisibilityCondition(min_visible_pages=1))
        selenium_executor._driver.switch_to.window(visible_pages[0].handle)

        driver = selenium_executor._driver
        # 1) 找到 shadow host
        host = driver.find_element(By.CSS_SELECTOR, "wx-input.query-bar--input_native")
        # 2) 拿到 shadow root
        shadow = driver.execute_script("return arguments[0].shadowRoot", host)
        # 3) 在 shadow root 里定位 <div role="textbox">
        textbox = shadow.find_element(By.CSS_SELECTOR, "div[role='textbox']")
        textbox.click()
        textbox.send_keys("拿铁")

    # try:
    #     # 构建操作序列
    #     operations = [
    #         # 查找搜索按钮
    #         OperationItem("find", method="css selector", selector="wx-view.query.menu-bar--query", timeout=10),
    #         # 点击搜索按钮并等待新窗口
    #         OperationItem("click", wait_for_new_window=True, timeout=10),
    #         # 等待新页面渲染
    #         OperationItem("wait_for_page_render", timeout=10),
    #         # 查找输入框
    #         OperationItem("find", method="css selector", selector="wx-input.query-bar--input_native[confirm-type='search']", timeout=10),
    #         # 输入搜索文本
    #         OperationItem("input", text="拿铁"),
    #         # 查找搜索按钮
    #         OperationItem("find", method="css selector", selector="#submit-button", timeout=10),
    #         # 点击搜索按钮
    #         OperationItem("click")
    #     ]
    #
    #     # 构建并执行操作序列
    #     sequence = OperationSequence(operations)
    #     results = sequence.execute(device)
    #
    #     # 打印结果
    #     for i, result in enumerate(results):
    #         print(f"Step {i + 1}: {'Success' if result['success'] else 'Failed'}")
    #         if not result['success']:
    #             print(f"Error: {result['error']}")
    #         print(f"Time: {result['elapsed']:.2f}s")

    finally:
        # 断开设备连接
        device.disconnect()


if __name__ == "__main__":
    main()
