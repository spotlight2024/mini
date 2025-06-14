import time
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

class AndroidDevice:
    def __init__(self, driver):
        """
        初始化Android设备
        :param driver: Selenium WebDriver实例
        """
        self.driver = driver
        self.context = {}
        self.wait = WebDriverWait(self.driver, 10)  # 默认等待10秒

    def wait_for_new_window(self, timeout=10, old_handles=None):
        """
        等待新窗口出现并切换到新窗口
        :param timeout: 超时时间（秒）
        :param old_handles: 旧窗口句柄集合
        :return: 新窗口句柄，如果超时则返回None
        """
        try:
            if old_handles is None:
                old_handles = set(self.driver.window_handles)
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                new_handles = set(self.driver.window_handles)
                if new_handles - old_handles:
                    new_handle = (new_handles - old_handles).pop()
                    self.driver.switch_to.window(new_handle)
                    return new_handle
                time.sleep(0.5)
            return None
        except Exception as e:
            logging.error(f"[AndroidDevice] wait_for_new_window failed: {e}")
            return None

    def wait_for_page_load(self, timeout=10):
        """
        等待页面加载完成
        :param timeout: 超时时间（秒）
        :return: 是否加载完成
        """
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.driver.execute_script("return document.readyState") == "complete":
                    return True
                time.sleep(0.5)
            return False
        except Exception as e:
            logging.error(f"[AndroidDevice] wait_for_page_load failed: {e}")
            return False

    def execute_script(self, script):
        """
        执行JavaScript脚本
        :param script: 要执行的脚本
        :return: 脚本执行结果
        """
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            logging.error(f"[AndroidDevice] execute_script failed: {e}")
            return None

    def get_window_handles(self):
        """
        获取所有窗口句柄
        :return: 窗口句柄列表
        """
        try:
            return self.driver.window_handles
        except Exception as e:
            logging.error(f"[AndroidDevice] get_window_handles failed: {e}")
            return []

    def wait_for_element(self, method, selector, timeout=10):
        """
        等待元素出现
        :param method: 定位方法（css selector, xpath等）
        :param selector: 选择器
        :param timeout: 超时时间（秒）
        :return: 元素对象，如果超时则返回None
        """
        try:
            from selenium.webdriver.common.by import By
            by_method = getattr(By, method.upper().replace(" ", "_"))
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by_method, selector))
            )
            return element
        except TimeoutException:
            logging.warning(f"[AndroidDevice] Element not found: {method}={selector}")
            return None
        except Exception as e:
            logging.error(f"[AndroidDevice] wait_for_element failed: {e}")
            return None

    def handle_common_popups(self):
        """
        处理常见的弹窗
        """
        try:
            # 处理常见的弹窗选择器
            popup_selectors = [
                "button.close",
                ".modal-close",
                ".popup-close",
                "#cookie-consent button",
                ".cookie-banner button"
            ]
            
            for selector in popup_selectors:
                try:
                    element = self.wait_for_element("css selector", selector, timeout=3)
                    if element and element.is_displayed():
                        element.click()
                        logging.info(f"[AndroidDevice] Closed popup: {selector}")
                except:
                    continue
        except Exception as e:
            logging.warning(f"[AndroidDevice] handle_common_popups failed: {e}") 