"""
豆包页面类 - 实现豆包网站的基础页面操作
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from hybrid_driver.business_framework.pages.base_page import BasePage


class DoubaoHomePage(BasePage):
    """豆包首页"""

    def __init__(self, driver: WebDriver, page_manager, site_config: dict, session_id: str):
        super().__init__(driver, page_manager, site_config, session_id)
        self.url = site_config["home_url"]
        self.locators = {
            "app_root": (By.CSS_SELECTOR, "body"),
        }

    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return "doubao" in self.driver.current_url.lower()
        except Exception:
            return False

    def navigate_to(self) -> "DoubaoHomePage":
        """导航到豆包首页"""
        self.logger.info(f"开始打开 {self.url}")
        self.driver.get(self.url)
        return self

    def wait_until_loaded(self) -> "DoubaoHomePage":
        """等待页面主结构渲染完成"""
        self.wait_for_element(*self.locators["app_root"], description="豆包页面主体")
        return self
