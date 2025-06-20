import logging
from typing import Optional, Any, Callable
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)
from log_config import get_logger

# 获取logger实例
logger = get_logger(__name__)


class WaitUtils:
    """等待工具类，提供最优的等待机制"""
    
    # 默认超时时间（秒）
    DEFAULT_TIMEOUT = 10
    # 默认轮询间隔（秒）
    DEFAULT_POLL_FREQUENCY = 0.5
    # 需要忽略的异常
    IGNORED_EXCEPTIONS = (
        StaleElementReferenceException,
        ElementClickInterceptedException,
        ElementNotInteractableException
    )

    @classmethod
    def wait_for_element(
        cls,
        driver,
        by: str,
        value: str,
        timeout: int = DEFAULT_TIMEOUT,
        poll_frequency: float = DEFAULT_POLL_FREQUENCY,
        condition: str = "presence"
    ) -> Optional[Any]:
        """
        等待元素满足指定条件
        
        Args:
            driver: WebDriver 实例
            by: 定位方式
            value: 定位值
            timeout: 超时时间
            poll_frequency: 轮询间隔
            condition: 等待条件，可选值：
                - presence: 元素存在
                - visible: 元素可见
                - clickable: 元素可点击
                - selected: 元素被选中
                - enabled: 元素可用
        """
        try:
            wait = WebDriverWait(
                driver,
                timeout=timeout,
                poll_frequency=poll_frequency,
                ignored_exceptions=cls.IGNORED_EXCEPTIONS
            )
            
            conditions = {
                "presence": EC.presence_of_element_located((by, value)),
                "visible": EC.visibility_of_element_located((by, value)),
                "clickable": EC.element_to_be_clickable((by, value)),
                "selected": EC.element_located_to_be_selected((by, value)),
                "enabled": EC.element_to_be_clickable((by, value))
            }
            
            if condition not in conditions:
                raise ValueError(f"Unsupported condition: {condition}")
                
            element = wait.until(conditions[condition])
            logger.info(f"Element found: {by}={value}, condition={condition}")
            return element
            
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {by}={value}, condition={condition}")
            return None
        except Exception as e:
            logger.error(f"Error waiting for element: {by}={value}, error={str(e)}")
            return None

    @classmethod
    def wait_for_page_load(
        cls,
        driver,
        timeout: int = DEFAULT_TIMEOUT,
        poll_frequency: float = DEFAULT_POLL_FREQUENCY
    ) -> bool:
        """
        等待页面加载完成
        
        Args:
            driver: WebDriver 实例
            timeout: 超时时间
            poll_frequency: 轮询间隔
        """
        try:
            wait = WebDriverWait(
                driver,
                timeout=timeout,
                poll_frequency=poll_frequency,
                ignored_exceptions=cls.IGNORED_EXCEPTIONS
            )
            
            # 等待 document.readyState 为 complete
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
            # 等待 jQuery（如果存在）加载完成
            try:
                wait.until(lambda d: d.execute_script("return jQuery.active == 0"))
            except:
                pass
                
            # 等待 Angular（如果存在）加载完成
            try:
                wait.until(lambda d: d.execute_script("return angular.element(document).injector().get('$http').pendingRequests.length === 0"))
            except:
                pass
                
            logger.info("Page loaded successfully")
            return True
            
        except TimeoutException:
            logger.warning("Timeout waiting for page load")
            return False
        except Exception as e:
            logger.error(f"Error waiting for page load: {str(e)}")
            return False

    @classmethod
    def wait_for_new_window(
        cls,
        driver,
        timeout: int = DEFAULT_TIMEOUT,
        poll_frequency: float = DEFAULT_POLL_FREQUENCY
    ) -> Optional[str]:
        """
        等待新窗口打开
        
        Args:
            driver: WebDriver 实例
            timeout: 超时时间
            poll_frequency: 轮询间隔
        """
        try:
            wait = WebDriverWait(
                driver,
                timeout=timeout,
                poll_frequency=poll_frequency,
                ignored_exceptions=cls.IGNORED_EXCEPTIONS
            )
            
            # 记录当前窗口句柄
            old_handles = set(driver.window_handles)
            
            # 等待新窗口出现
            def new_window_present(d):
                new_handles = set(d.window_handles)
                return len(new_handles) > len(old_handles)
                
            wait.until(new_window_present)
            
            # 获取新窗口句柄
            new_handles = set(driver.window_handles)
            new_handle = (new_handles - old_handles).pop()
            
            # 切换到新窗口
            driver.switch_to.window(new_handle)
            
            logger.info(f"New window opened and switched: {new_handle}")
            return new_handle
            
        except TimeoutException:
            logger.warning("Timeout waiting for new window")
            return None
        except Exception as e:
            logger.error(f"Error waiting for new window: {str(e)}")
            return None

    @classmethod
    def wait_for_condition(
        cls,
        driver,
        condition: Callable,
        timeout: int = DEFAULT_TIMEOUT,
        poll_frequency: float = DEFAULT_POLL_FREQUENCY
    ) -> bool:
        """
        等待自定义条件满足
        
        Args:
            driver: WebDriver 实例
            condition: 自定义条件函数
            timeout: 超时时间
            poll_frequency: 轮询间隔
        """
        try:
            wait = WebDriverWait(
                driver,
                timeout=timeout,
                poll_frequency=poll_frequency,
                ignored_exceptions=cls.IGNORED_EXCEPTIONS
            )
            
            result = wait.until(condition)
            logger.info("Custom condition met")
            return result
            
        except TimeoutException:
            logger.warning("Timeout waiting for custom condition")
            return False
        except Exception as e:
            logger.error(f"Error waiting for custom condition: {str(e)}")
            return False 