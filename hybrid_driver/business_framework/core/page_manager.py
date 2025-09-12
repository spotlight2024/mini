"""
页面管理器 - 处理多页面切换和操作
"""
import time
import logging
from typing import Optional, Dict, Any, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException

from hybrid_driver.log_config import get_logger


class PageManager:
    """页面管理器 - 处理多页面切换和操作"""
    
    def __init__(self, driver: WebDriver, session_id: str):
        self.driver = driver
        self.session_id = session_id
        self.pages = {}
        self.current_page = None
        self.main_window = None
        self.logger = get_logger(f"PageManager-{session_id}")
    
    def register_main_page(self, page_name: str = "main") -> 'PageManager':
        """注册主页面"""
        self.main_window = self.driver.current_window_handle
        self.pages[page_name] = {
            'handle': self.main_window,
            'url': self.driver.current_url,
            'title': self.driver.title,
            'timestamp': time.time()
        }
        self.current_page = page_name
        self.logger.info(f"主页面已注册: {page_name}")
        return self
    
    def wait_for_new_window(self, timeout: int = 10) -> Optional[str]:
        """等待新窗口出现"""
        self.logger.info("等待新窗口出现...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_windows = self.driver.window_handles
            if len(current_windows) > len(self.pages):
                new_window = [w for w in current_windows if w not in [p['handle'] for p in self.pages.values()]][0]
                self.logger.info(f"新窗口已出现: {new_window}")
                return new_window
        
        raise TimeoutException("新窗口未在指定时间内出现")
    
    def switch_to_new_window(self, page_name: str = "new_page") -> 'PageManager':
        """切换到新窗口"""
        new_window = self.wait_for_new_window()
        
        # 切换到新窗口
        self.driver.switch_to.window(new_window)

        current_url = self.driver.current_url
        
        # 注册新页面
        self.pages[page_name] = {
            'handle': new_window,
            'url': current_url,
            'title': self.driver.title,
            'timestamp': time.time()
        }
        
        self.current_page = page_name
        self.logger.info(f"已切换到新页面: {page_name}")
        self.logger.info(f"新页面URL: {current_url}")
        
        return self
    
    def switch_to_page(self, page_name: str) -> 'PageManager':
        """切换到指定页面"""
        if page_name not in self.pages:
            raise ValueError(f"页面 {page_name} 未注册")
        
        self.driver.switch_to.window(self.pages[page_name]['handle'])
        self.current_page = page_name
        self.logger.info(f"已切换到页面: {page_name}")
        return self
    
    def switch_to_main(self) -> 'PageManager':
        """切换回主页面"""
        return self.switch_to_page('main')
    
    def close_current_page(self) -> 'PageManager':
        """关闭当前页面"""
        if self.current_page != 'main':
            self.driver.close()
            self.logger.info(f"已关闭页面: {self.current_page}")
            del self.pages[self.current_page]
            self.current_page = 'main'
            self.switch_to_main()
        return self
    
    def get_page_info(self) -> 'PageManager':
        """获取所有页面信息"""
        self.logger.info("📊 页面信息统计:")
        for name, info in self.pages.items():
            self.logger.info(f"  {name}: {info['url']} (标题: {info['title']})")
        return self
    
    def get_current_page_url(self) -> str:
        """获取当前页面URL"""
        return self.driver.current_url
    
    def get_current_page_title(self) -> str:
        """获取当前页面标题"""
        return self.driver.title
