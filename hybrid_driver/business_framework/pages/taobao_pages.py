"""
淘宝页面类 - 实现淘宝网站的各种页面操作
"""
import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from hybrid_driver.business_framework.pages.base_page import BasePage
from hybrid_driver.log_config import get_logger


class TaobaoHomePage(BasePage):
    """淘宝首页"""
    
    def __init__(self, driver: WebDriver, page_manager, site_config: dict, session_id: str):
        super().__init__(driver, page_manager, site_config, session_id)
        self.url = site_config['home_url']
        
        # 页面元素定位器
        self.locators = {
            'search_button': (By.CLASS_NAME, "image-search-icon-outerMode"),
            'file_input': (By.ID, "image-search-custom-file-input"),
            'upload_button': (By.ID, "image-search-upload-button")
        }
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return "taobao" in self.driver.current_url.lower()
        except:
            return False
    
    def navigate_to(self) -> 'TaobaoHomePage':
        """导航到淘宝首页"""
        self.logger.info(f"开始打开 {self.url}")
        self.driver.get(self.url)
        return self
    
    def click_search_button(self) -> 'TaobaoHomePage':
        """点击搜同款按钮"""
        return self.move_and_click(
            *self.locators['search_button'], 
            "搜同款按钮"
        )
    
    def wait_for_file_input(self) -> 'TaobaoHomePage':
        """等待文件输入框出现"""
        self.wait_for_element(
            *self.locators['file_input'], 
            description="文件输入框"
        )
        return self
    
    def upload_image(self, file_path: str) -> 'TaobaoHomePage':
        """上传图片"""
        return self.upload_file(
            *self.locators['file_input'], 
            file_path, 
            "图片文件"
        )
    
    def click_upload_button(self) -> 'TaobaoHomePage':
        """点击上传按钮"""
        return self.move_and_click(
            *self.locators['upload_button'], 
            "搜索按钮"
        )


class TaobaoSearchPage(BasePage):
    """淘宝搜索结果页面"""
    
    def __init__(self, driver: WebDriver, page_manager, site_config: dict, session_id: str):
        super().__init__(driver, page_manager, site_config, session_id)
        
        # 搜索结果页面元素
        self.locators = {
            'filter_button': (By.CLASS_NAME, "filter-button"),
            'price_filter': (By.CLASS_NAME, "price-filter"),
            'price_range_100_500': (By.CLASS_NAME, "price-range-100-500"),
            'apply_filter': (By.CLASS_NAME, "apply-filter"),
            'product_items': (By.CLASS_NAME, "product-item"),
            'sort_button': (By.CLASS_NAME, "sort-button"),
            'sort_by_price': (By.CLASS_NAME, "sort-by-price"),
            # 基于HTML结构添加商品相关定位器
            'product_links': (By.CSS_SELECTOR, "a[data-spm-act-id]"),
            'product_titles': (By.CSS_SELECTOR, "span"),
            'product_cards': (By.CSS_SELECTOR, "div[data-appeared='true']")
        }
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return "search" in self.driver.current_url.lower() or "result" in self.driver.current_url.lower()
        except:
            return False
    
    def click_filter_button(self) -> 'TaobaoSearchPage':
        """点击筛选按钮"""
        return self.click_element(
            *self.locators['filter_button'], 
            "筛选按钮"
        )
    
    def select_price_range(self, price_range: str = "100-500") -> 'TaobaoSearchPage':
        """选择价格范围"""
        if price_range == "100-500":
            return self.click_element(
                *self.locators['price_range_100_500'], 
                "价格范围100-500"
            )
        # 可以添加其他价格范围
        return self
    
    def apply_filter(self) -> 'TaobaoSearchPage':
        """应用筛选"""
        return self.click_element(
            *self.locators['apply_filter'], 
            "应用筛选"
        )
    
    def sort_by_price(self) -> 'TaobaoSearchPage':
        """按价格排序"""
        return (self.click_element(*self.locators['sort_button'], "排序按钮")
                .click_element(*self.locators['sort_by_price'], "按价格排序"))
    
    def get_product_count(self) -> int:
        """获取商品数量"""
        try:
            products = self.driver.find_elements(*self.locators['product_items'])
            count = len(products)
            self.logger.info(f"找到 {count} 个商品")
            return count
        except Exception as e:
            self.logger.error(f"获取商品数量失败: {e}")
            return 0

    def page_source(self) -> str:
        """获取页面源码"""
        return self.driver.page_source
    
    def get_product_titles(self) -> list:
        """获取商品标题列表"""
        try:

            # 方法1：通过商品卡片获取标题
            titles = []
            
            # 查找所有包含商品信息的链接
            product_links = self.driver.find_elements(By.CSS_SELECTOR, "a[data-spm-act-id]")
            self.logger.info(f"找到 {len(product_links)} 个商品链接")
            
            for i, link in enumerate(product_links):  # 获取所有商品
                try:
                    # 在链接内查找标题文本
                    title_elements = link.find_elements(By.CSS_SELECTOR, "span")
                    for span in title_elements:
                        text = span.text.strip()
                        # 过滤掉空文本和太短的文本
                        if text and len(text) > 5 and not text.isdigit():
                            titles.append(text)
                            # self.logger.info(f"商品 {i+1} 标题: {text}")
                            break  # 找到第一个有效标题就跳出
                except Exception as e:
                    self.logger.warning(f"获取第 {i+1} 个商品标题失败: {e}")
                    continue
            
            # 方法2：如果方法1没有找到，尝试通过其他选择器
            if not titles:
                self.logger.info("尝试其他方式获取商品标题...")
                # 查找所有包含中文的span元素
                all_spans = self.driver.find_elements(By.CSS_SELECTOR, "span")
                for span in all_spans:
                    text = span.text.strip()
                    # 过滤条件：包含中文、长度适中、不包含特殊字符
                    if (text and 
                        len(text) > 10 and len(text) < 100 and 
                        any('\u4e00' <= char <= '\u9fff' for char in text) and
                        not any(char in text for char in ['¥', '$', '￥', '元', '件', '个'])):
                        titles.append(text)
                        # self.logger.info(f"备用方法找到标题: {text}")
                        if len(titles) >= 10:  # 限制数量
                            break
            
            self.logger.info(f"总共获取到 {len(titles)} 个商品标题")
            return titles
            
        except Exception as e:
            self.logger.error(f"获取商品标题失败: {e}")
            return []
    
    def print_product_titles_to_log(self, titles: list = None) -> int:
        """打印商品标题到日志"""
        try:
            # 如果没有传入titles，则获取一次
            if titles is None:
                titles = self.get_product_titles()
            
            if titles:
                self.logger.info("=" * 60)
                self.logger.info("🏷️  搜索结果 - 商品标题列表:")
                self.logger.info("=" * 60)
                
                for i, title in enumerate(titles, 1):
                    self.logger.info(f"📦 商品 {i:2d}: {title}")
                
                self.logger.info("=" * 60)
                self.logger.info(f"✅ 共找到 {len(titles)} 个商品标题")
                self.logger.info("=" * 60)
                
                return len(titles)
            else:
                self.logger.warning("⚠️ 未找到任何商品标题")
                return 0
                
        except Exception as e:
            self.logger.error(f"打印商品标题失败: {e}")
            return 0