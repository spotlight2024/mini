"""
页面基类 - 定义通用操作
"""
import time
import logging
from typing import Optional, Union, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import wait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains

from hybrid_driver.log_config import get_logger


class BasePage:
    """页面基类 - 定义通用操作"""
    
    def __init__(self, driver: WebDriver, page_manager, site_config: dict, session_id: str):
        self.driver = driver
        self.page_manager = page_manager
        self.site_config = site_config
        self.session_id = session_id
        self.logger = get_logger(f"BasePage-{session_id}")
        self.actions = ActionChains(driver)
    
    def wait_for_element(self, by: Union[str, By], value: str, timeout: int = 10, description: str = "") -> Optional[WebElement]:
        """等待元素出现"""
        try:
            element = wait.WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            self.logger.info(f"找到元素: {description or f'{by}={value}'}")
            return element
        except Exception as e:
            self.logger.error(f"未找到元素 {description or f'{by}={value}'}: {e}")
            raise e
    
    def wait_for_clickable(self, by: Union[str, By], value: str, timeout: int = 10, description: str = "") -> Optional[WebElement]:
        """等待元素可点击"""
        try:
            element = wait.WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            self.logger.info(f"元素可点击: {description or f'{by}={value}'}")
            return element
        except Exception as e:
            self.logger.error(f"元素不可点击 {description or f'{by}={value}'}: {e}")
            raise e
    
    def click_element(self, by: Union[str, By], value: str, description: str = "") -> 'BasePage':
        """点击元素"""
        element = self.wait_for_clickable(by, value, description=description)
        element.click()
        self.logger.info(f"成功点击: {description or f'{by}={value}'}")
        return self
    
    def move_and_click(self, by: Union[str, By], value: str, description: str = "") -> 'BasePage':
        """移动鼠标并点击"""
        element = self.wait_for_clickable(by, value, description=description)
        self.actions.move_to_element(element).click().perform()
        self.logger.info(f"移动并点击: {description or f'{by}={value}'}")
        return self
    
    def upload_file(self, by: Union[str, By], value: str, file_path: str, description: str = "") -> 'BasePage':
        """上传文件"""
        element = self.wait_for_element(by, value, description=description)
        
        # 显示隐藏的file input
        self.driver.execute_script("""
            arguments[0].style.display='block';
            arguments[0].style.visibility='visible';
            arguments[0].removeAttribute('disabled');
        """, element)
        
        element.send_keys(file_path)
        self.logger.info(f"文件上传成功: {file_path}")
        return self
    
    def get_page_info(self) -> 'BasePage':
        """获取页面信息"""
        try:
            title = self.driver.title
            current_url = self.driver.current_url
            self.logger.info(f"页面标题: {title}")
            self.logger.info(f"当前URL: {current_url}")
        except Exception as e:
            self.logger.error(f"页面信息获取异常: {e}")
        return self
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成 - 子类需要实现"""
        raise NotImplementedError("子类必须实现is_loaded方法")
