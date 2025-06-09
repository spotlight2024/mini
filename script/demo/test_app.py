import logging
from dataclasses import dataclass
from typing import List, Dict, Any

import adbutils
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from web_driver import SeleniumWebDriver


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
                self.is_active and
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
    1) 等待 timeout 秒，看是否出现带有 “.ad-pop-index--close-icon-new” 这个 class 的 close 按钮。
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

            # # 记录页面信息
            # logging.info(
            #     f"窗口状态 - Handle: {page.handle} | "
            #     f"URL: {page.url} | "
            #     f"Title: {page.title} | "
            #     f"可见性: {page.is_actually_visible} | "
            #     f"视口大小: {page.viewport_width}x{page.viewport_height} | "
            #     f"焦点状态: {page.is_active} | "
            #     f"隐藏状态: {page.is_hidden}"
            # )

            if page.is_foreground:
                logging.info(f"前台页面 - Handle: {page.handle} | URL: {page.url} | title: {page.title}")

        except Exception as e:
            logging.error(f"检查页面状态时出错: {str(e)}")
            continue

        if page.is_actually_visible:
            visible_pages.append(page)

    # 输出可见页面统计
    if visible_pages:
        logging.info(f"可见页面统计 - 总数: {len(visible_pages)}")
        for page in visible_pages:
            logging.info(f"可见页面 - URL: {page.url}")

    return visible_pages


def test_real_connect():
    driver = SeleniumWebDriver()
    devices = adbutils.adb.device_list()
    logging.info(f"start connect")
    for device in devices:
        logging.info(f"device serial: ${device.serial}")
        logging.info(f"device info: ${device.app_current()}")
        result = driver.connect(device.serial)
        logging.info(f"connect result: ${result}")
        chrome_driver = driver.driver
        chrome_driver.implicitly_wait(3)

        wait = WebDriverWait(chrome_driver, 10)  # 最长等待 10 秒
        logging.info(f"current handle: ${chrome_driver.current_window_handle}")

        # 等待页面加载完成并获取可见页面
        visible_pages = wait.until(PageVisibilityCondition(min_visible_pages=1))
        logging.info(f"visible pages: {visible_pages}")

        chrome_driver.switch_to.window(visible_pages[0].handle)

        # logging.info(f"is popup : ${chrome_driver.find_element(By.CSS_SELECTOR,".wx-popup-pannel").is_displayed()}")
        try_close_popup(chrome_driver, 3)


if __name__ == "__main__":
    test_real_connect()
