"""
淘宝业务类 - 实现淘宝网站的各种业务逻辑
"""
import time
from typing import Optional
from pathlib import Path
from selenium.webdriver.common.by import By

from business.base_business import BaseBusiness
from pages.taobao_pages import TaobaoHomePage, TaobaoSearchPage
from hybrid_driver.log_config import get_logger


class TaobaoBusiness(BaseBusiness):
    """淘宝业务类"""
    
    def __init__(self, session_id: str):
        # 淘宝网站配置
        site_config = {
            'site_name': 'taobao',
            'home_url': 'https://www.taobao.com/',
            'hub_url': 'http://172.16.1.129:30444/wd/hub',
            'timeout': 30,
            'implicit_wait': 10,
            'page_load_timeout': 30,
            'webdriver_mode': 'remote',
            'browser_version': '138',
            'platform_name': 'linux'
        }
        super().__init__(site_config, session_id)
        self.home_page = None
        self.search_page = None
    
    def initialize_pages(self) -> 'TaobaoBusiness':
        """初始化页面对象"""
        driver = self.get_driver()
        if not driver:
            raise RuntimeError("WebDriver未初始化")
        
        self.home_page = TaobaoHomePage(driver, self.page_manager, self.site_config, self.session_id)
        self.search_page = TaobaoSearchPage(driver, self.page_manager, self.site_config, self.session_id)
        
        return self
    
    def execute_search_business(self, file_path: str = "logo.png") -> bool:
        """执行搜索业务"""
        try:
            # 1. 导航到首页
            self.home_page.navigate_to()
            
            # 2. 注册主页面
            self.page_manager.register_main_page("taobao_home")
            
            # 3. 执行图片搜索
            (self.home_page
             .click_search_button()
             .wait_for_file_input()
             .upload_image(file_path)
             .click_upload_button())
            
            # 4. 等待新页面并切换
            self.page_manager.wait_for_new_window()
            self.page_manager.switch_to_new_window("search_results")


            self.logger.info(f"页面源码: {self.search_page.page_source()}")


            
            # # 5. 在新页面中操作
            # (self.search_page
            #  .click_filter_button()
            #  .select_price_range("100-500")
            #  .apply_filter()
            #  .sort_by_price())
            
            # # 6. 获取搜索结果
            # product_count = self.search_page.get_product_count()
            
            # 7. 返回主页面
            self.page_manager.switch_to_main()

            return True
            
        except Exception as e:
            self.logger.error(f"搜索业务失败: {e}")
            return False
    
    def execute_business_flow(self) -> bool:
        """执行业务流程"""
        return self.execute_search_business("logo.png")
    
    def execute_image_search_with_actions(self, file_path: str = "logo.png") -> bool:
        """使用ActionChains执行图片搜索业务"""
        try:
            # 获取ActionChains和WebDriverChain
            actions = self.get_action_chains()
            chain = self.get_webdriver_chain()
            
            if not actions or not chain:
                raise RuntimeError("ActionChains或WebDriverChain未初始化")
            
            # 1. 检查IP信息
            chain.check_ip_info()
            
            # 2. 导航到淘宝首页
            chain.navigate_to('https://www.taobao.com/')
            
            # 3. 注册主页面
            self.page_manager.register_main_page()
            
            # 4. 使用ActionChains执行图片搜索
            (actions
             .log("🔍 开始图片搜索流程（使用ActionChains）")
             .move_to_element(By.CLASS_NAME, "image-search-icon-outerMode", "搜同款按钮")
             .click(By.CLASS_NAME, "image-search-icon-outerMode", "搜同款按钮")
             .perform())
            
            # 5. 等待文件输入框
            chain.wait_for_element(By.ID, "image-search-custom-file-input", description="文件输入框")
            
            # 6. 上传图片
            chain.upload_file(By.ID, "image-search-custom-file-input", file_path, "图片文件")
            
            # 7. 点击上传按钮并等待新页面
            (actions
             .log("⏳ 使用ActionChains点击搜索按钮...")
             .move_to_element(By.ID, "image-search-upload-button", "搜索按钮")
             .click(By.ID, "image-search-upload-button", "搜索按钮")
             .perform())
            
            # 8. 等待新页面并切换
            self.page_manager.wait_for_new_window()
            self.page_manager.switch_to_new_window("search_results")

            # 9. 获取并打印商品标题
            self.logger.info("🔍 开始获取搜索结果中的商品标题...")
            product_count = self.search_page.print_product_titles_to_log()
            
            # 10. 获取页面基本信息
            chain.get_page_info()

            

            return True
            
        except Exception as e:
            self.logger.error(f"图片搜索业务失败: {e}")
            return False
