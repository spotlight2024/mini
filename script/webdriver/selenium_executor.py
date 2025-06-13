import logging
from dataclasses import dataclass
from typing import Optional, Any, List, Dict

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from webdriver.popup_handler import PopupHandler
from webdriver.web_executor import WebExecutor

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

    def find_elements(self, by: str, value: str) -> Optional[List[WebElement]]:
        """查找元素"""
        if not self._driver:
            logging.warning("[SeleniumWebExecutor] 查找元素失败: WebDriver 未初始化")
            return None
        try:
            elements = self._driver.find_elements(by, value)
            logging.debug(f"[SeleniumWebExecutor] 元素查找成功 by={by}, value={value}")
            return elements
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

if __name__ == "__main__":
    from device_pool import DevicePool

    with DevicePool() as device_pool:
        device = DevicePool().connect("JJGICIN7QOAELNGI")
        
        # 类型检查和转换
        selenium_executor: SeleniumWebExecutor = device._web_execute
        wait = WebDriverWait(selenium_executor._driver, 10)  # 最长等待 10 秒
        logging.info(f"current handle: {selenium_executor._driver.current_window_handle}")

        # 等待页面加载完成并获取可见页面
        visible_pages = wait.until(PageVisibilityCondition(min_visible_pages=1))
        selenium_executor._driver.switch_to.window(visible_pages[0].handle)

        logging.info(f"visible pages: {visible_pages}")
        # logging.info(f"current handle: {selenium_executor._driver.page_source}")

        elements = device.find_element(By.CSS_SELECTOR, "wx-view.menu-product_name.product--menu-product_name")
        logging.info(f"[SeleniumWebExecutor] <UNK> element={elements}")
        device.disconnect()
