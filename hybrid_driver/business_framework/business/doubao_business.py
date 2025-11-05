"""
豆包业务类 - 实现打开豆包页面的基础流程
"""
from time import sleep
from typing import Optional, Dict, Any

from hybrid_driver.business_framework.business.base_business import BaseBusiness
from hybrid_driver.business_framework.pages.doubao_pages import DoubaoHomePage


class DoubaoBusiness(BaseBusiness):
    """豆包业务类"""

    def __init__(self, session_id: str, user_id: str, site_overrides: Optional[Dict[str, Any]] = None):
        site_config = {
            "site_name": "doubao",
            "home_url": "https://www.doubao.com/chat",
            "hub_url": "http://172.16.1.129:30444/wd/hub",
            "timeout": 30,
            "implicit_wait": 10,
            "page_load_timeout": 30,
            "webdriver_mode": "remote",
            "browser_version": "138",
            "platform_name": "linux",
        }
        if site_overrides:
            site_config.update(site_overrides)
        super().__init__(site_config, session_id, user_id)
        self.home_page: Optional[DoubaoHomePage] = None

    def initialize_pages(self) -> "DoubaoBusiness":
        """初始化页面对象"""
        driver = self.get_driver()
        if not driver:
            raise RuntimeError("WebDriver未初始化")

        self.home_page = DoubaoHomePage(driver, self.page_manager, self.site_config, self.session_id)
        return self

    def open_home_page(self) -> bool:
        """打开豆包首页"""
        if not self.home_page:
            raise RuntimeError("页面未初始化，请先调用 initialize_pages()")

        try:
            self.home_page.navigate_to().wait_until_loaded()
            self.page_manager.register_main_page("doubao_home")
            sleep(120)
            self.logger.info("豆包首页打开完成")
            return True
        except Exception as exc:
            self.logger.error(f"打开豆包首页失败: {exc}")
            return False

    def execute_business_flow(self) -> bool:
        """执行业务流程"""
        return self.open_home_page()
