import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

class WebDriverUtils:
    @staticmethod
    def wait_for_element(driver, by, value, timeout=10, trace_id=None):
        """
        等待元素出现
        :param driver: WebDriver实例
        :param by: 定位方式
        :param value: 定位值
        :param timeout: 超时时间
        :param trace_id: 追踪ID
        :return: 元素对象或None
        """
        try:
            logging.info(f"[WebDriverUtils] 开始等待元素: by={by}, value={value}, timeout={timeout}, trace_id={trace_id}")
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            logging.info(f"[WebDriverUtils] 元素已找到: by={by}, value={value}, trace_id={trace_id}")
            return element
        except TimeoutException:
            logging.warning(f"[WebDriverUtils] 等待元素超时: by={by}, value={value}, timeout={timeout}, trace_id={trace_id}")
            return None
        except WebDriverException as e:
            logging.error(f"[WebDriverUtils] WebDriver异常: {str(e)}, by={by}, value={value}, trace_id={trace_id}")
            return None
        except Exception as e:
            logging.error(f"[WebDriverUtils] 未知异常: {str(e)}, by={by}, value={value}, trace_id={trace_id}")
            return None

    @staticmethod
    def wait_for_page_load(driver, timeout=10):
        """
        等待页面加载完成
        :param driver: WebDriver实例
        :param timeout: 超时时间
        :return: 是否加载完成
        """
        try:
            logging.info(f"[WebDriverUtils] 等待页面加载: timeout={timeout}")
            start_time = time.time()
            while time.time() - start_time < timeout:
                if driver.execute_script("return document.readyState") == "complete":
                    logging.info("[WebDriverUtils] 页面加载完成")
                    return True
                time.sleep(0.5)
            logging.warning(f"[WebDriverUtils] 页面加载超时: timeout={timeout}")
            return False
        except Exception as e:
            logging.error(f"[WebDriverUtils] 等待页面加载异常: {str(e)}")
            return False

    @staticmethod
    def wait_for_new_window(driver, timeout=10, old_handles=None):
        """
        等待新窗口出现
        :param driver: WebDriver实例
        :param timeout: 超时时间
        :param old_handles: 旧窗口句柄集合
        :return: 新窗口句柄或None
        """
        try:
            logging.info(f"[WebDriverUtils] 等待新窗口: timeout={timeout}")
            if old_handles is None:
                old_handles = set(driver.window_handles)
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                new_handles = set(driver.window_handles)
                if new_handles - old_handles:
                    new_handle = (new_handles - old_handles).pop()
                    driver.switch_to.window(new_handle)
                    logging.info(f"[WebDriverUtils] 切换到新窗口: {new_handle}")
                    return new_handle
                time.sleep(0.5)
            logging.warning(f"[WebDriverUtils] 等待新窗口超时: timeout={timeout}")
            return None
        except Exception as e:
            logging.error(f"[WebDriverUtils] 等待新窗口异常: {str(e)}")
            return None 