"""
业务基类 - 定义通用业务逻辑
"""
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from core.webdriver_manager import WebDriverManager
from core.page_manager import PageManager
from core.action_chains_wrapper import ActionChainsWrapper
from core.webdriver_chain import WebDriverChain
from hybrid_driver.log_config import get_logger


class BaseBusiness:
    """业务基类 - 定义通用业务逻辑"""
    
    def __init__(self, site_config: Dict[str, Any], session_id: str):
        self.site_config = site_config
        self.session_id = session_id
        self.driver_manager = None
        self.page_manager = None
        self.action_chains = None
        self.webdriver_chain = None
        self.logger = get_logger(f"BaseBusiness-{session_id}")
    
    def initialize(self) -> 'BaseBusiness':
        """初始化业务"""
        self.driver_manager = WebDriverManager(self.session_id, self.site_config)
        self.driver_manager.create_driver()
        self.page_manager = self.driver_manager.page_manager
        
        # 创建ActionChains和WebDriverChain
        self.action_chains = ActionChainsWrapper(self.driver_manager.driver, self.session_id)
        self.webdriver_chain = WebDriverChain(self.driver_manager.driver, self.session_id)
        
        return self
    
    def cleanup(self) -> 'BaseBusiness':
        """清理资源"""
        if self.driver_manager:
            self.driver_manager.quit()
        return self
    
    def execute_business_flow(self) -> bool:
        """执行业务流程 - 子类需要实现"""
        raise NotImplementedError("子类必须实现execute_business_flow方法")
    
    def get_driver(self):
        """获取WebDriver实例"""
        return self.driver_manager.driver if self.driver_manager else None
    
    def get_page_manager(self) -> Optional[PageManager]:
        """获取页面管理器"""
        return self.page_manager
    
    def get_action_chains(self) -> Optional[ActionChainsWrapper]:
        """获取ActionChains包装器"""
        return self.action_chains
    
    def get_webdriver_chain(self) -> Optional[WebDriverChain]:
        """获取WebDriverChain"""
        return self.webdriver_chain
