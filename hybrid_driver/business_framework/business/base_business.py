"""
业务基类 - 定义通用业务逻辑
"""
import logging
from pathlib import Path
import time
from typing import Any, Dict, Optional

from hybrid_driver.business_framework.core.action_chains_wrapper import (
    ActionChainsWrapper,
)
from hybrid_driver.business_framework.core.page_manager import PageManager
from hybrid_driver.business_framework.core.webdriver_chain import WebDriverChain
from hybrid_driver.business_framework.core.human_actions import (
    HumanMouse,
    HumanMouseConfig,
)
from hybrid_driver.business_framework.core.webdriver_manager import WebDriverManager
from hybrid_driver.log_config import get_logger


class BaseBusiness:
    """业务基类 - 定义通用业务逻辑"""
    
    def __init__(self, site_config: Dict[str, Any], session_id: str):
        self.site_config = site_config
        self.session_id = session_id
        self.webdriver_manager = None
        self.page_manager = None
        self.action_chains = None
        self.webdriver_chain = None
        self.logger = get_logger(f"BaseBusiness-{session_id}")
        self._human_mouse = None
        
        # 立即创建 WebDriverManager（但不创建driver）
        self._prepare_webdriver_manager()
    
    def _prepare_webdriver_manager(self) -> 'BaseBusiness':
        """准备 WebDriverManager（但不创建driver）"""
        self.webdriver_manager = WebDriverManager(self.session_id, self.site_config)
        return self
    
    def initialize(self) -> 'BaseBusiness':
        """初始化业务（创建driver和相关组件）"""
        if not self.webdriver_manager:
            self._prepare_webdriver_manager()
        
        # 创建driver
        self.webdriver_manager.create_driver()
        self.page_manager = self.webdriver_manager.page_manager
        
        # 创建ActionChains和WebDriverChain
        human_config = self.site_config.get("human_actions")
        human_config_obj = HumanMouseConfig.from_dict(human_config)
        human_mouse = None
        if human_config_obj.enabled:
            human_mouse = HumanMouse(
                self.webdriver_manager.driver,
                human_config_obj,
                logger=self.logger,
            )

        self.action_chains = ActionChainsWrapper(
            self.webdriver_manager.driver,
            self.session_id,
            human_mouse=human_mouse,
        )
        self.webdriver_chain = WebDriverChain(
            self.webdriver_manager.driver,
            self.session_id,
            human_action_config=human_config,
            human_mouse=human_mouse,
        )
        self._human_mouse = human_mouse

        return self
    
    def cleanup(self) -> 'BaseBusiness':
        """清理资源"""
        if self.webdriver_manager:
            self.webdriver_manager.quit()
        return self
    
    def execute_business_flow(self) -> bool:
        """执行业务流程 - 子类需要实现"""
        raise NotImplementedError("子类必须实现execute_business_flow方法")
    
    def get_driver(self):
        """获取WebDriver实例"""
        return self.webdriver_manager.driver if self.webdriver_manager else None
    
    def get_page_manager(self) -> Optional[PageManager]:
        """获取页面管理器"""
        return self.page_manager
    
    def get_action_chains(self) -> Optional[ActionChainsWrapper]:
        """获取ActionChains包装器"""
        return self.action_chains
    
    def get_webdriver_chain(self) -> Optional[WebDriverChain]:
        """获取WebDriverChain"""
        return self.webdriver_chain
    
    def get_chrome_options(self):
        """获取Chrome选项对象，可直接操作"""
        if not self.webdriver_manager:
            self._prepare_webdriver_manager()
        return self.webdriver_manager.prepare_chrome_options()
