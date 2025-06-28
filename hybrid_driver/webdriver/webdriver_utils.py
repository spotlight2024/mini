import time
from dataclasses import dataclass
from typing import Dict, Any

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from hybrid_driver.log_config import get_logger, setup_logging

logger = get_logger(__name__)

setup_logging()
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
            logger.info(f"开始等待元素: by={by}, value={value}, timeout={timeout}, trace_id={trace_id}")
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            logger.info(f"元素已找到: by={by}, value={value}, trace_id={trace_id}")
            return element
        except TimeoutException:
            logger.warning(f"等待元素超时: by={by}, value={value}, timeout={timeout}, trace_id={trace_id}")
            return None
        except WebDriverException as e:
            logger.error(f"WebDriver异常: {str(e)}, by={by}, value={value}, trace_id={trace_id}")
            return None
        except Exception as e:
            logger.error(f"未知异常: {str(e)}, by={by}, value={value}, trace_id={trace_id}")
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
            logger.info(f"等待页面加载: timeout={timeout}")
            start_time = time.time()
            while time.time() - start_time < timeout:
                if driver.execute_script("return document.readyState") == "complete":
                    logger.info("页面加载完成")
                    return True
                time.sleep(0.5)
            logger.warning(f"页面加载超时: timeout={timeout}")
            return False
        except Exception as e:
            logger.error(f"等待页面加载异常: {str(e)}")
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
            logger.info(f"等待新窗口: timeout={timeout}")
            if old_handles is None:
                old_handles = set(driver.window_handles)
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                new_handles = set(driver.window_handles)
                if new_handles - old_handles:
                    new_handle = (new_handles - old_handles).pop()
                    driver.switch_to.window(new_handle)
                    logger.info(f"切换到新窗口: {new_handle} , title : {driver.title}")
                    return new_handle
                time.sleep(0.5)
            logger.warning(f"等待新窗口超时: timeout={timeout}")
            return None
        except Exception as e:
            logger.error(f"等待新窗口异常: {str(e)}")
            return None

    @staticmethod
    def get_visible_page(driver, timeout=10) -> list[Page]:
        """
        获取可见页面，使用 Selenium 的等待机制
        :param driver: WebDriver实例
        :param timeout: 超时时间（秒）
        :return: 可见页面列表，超时返回空列表
        """
        start_time = time.time()
        try:
            wait = WebDriverWait(driver, timeout)
            
            def find_visible_pages(d):
                visible_pages_list = []
                # 先切换到第一个窗口，确保 handle 列表更新
                if d.window_handles:
                    d.switch_to.window(d.window_handles[0])
                    time.sleep(0.1)  # 给一点时间让 handle 列表更新
                
                for handle in d.window_handles:
                    d.switch_to.window(handle)
                    
                    # 获取页面状态
                    page_state = d.execute_script("""
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
                        url=d.current_url,
                        title=d.title,
                        is_visible=page_state['visibilityState'] == 'visible',
                        is_foreground=False,
                        viewport_width=page_state['viewportWidth'],
                        viewport_height=page_state['viewportHeight'],
                        is_active=page_state['isActive'],
                        is_hidden=page_state['hidden'],
                        state=page_state
                    )

                    logger.info(f"<page title>: {page.title}")
                    if ":VISIBLE" in d.title:
                        visible_pages_list.append(page)
                        break
                
                return visible_pages_list if visible_pages_list else None
            
            # 使用 WebDriverWait 等待可见页面出现
            visible_pages = wait.until(find_visible_pages)
            logger.info(f"找到可见页面 : {visible_pages}")
            return visible_pages
            
        except TimeoutException:
            logger.warning(f"获取可见页面超时: {timeout}秒")
            return []
        except Exception as e:
            logger.error(f"获取可见页面异常: {str(e)}")
            return []
        finally:
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000
            logger.info(f"Method get_visible_page executed in {execution_time_ms:.2f}ms")
        