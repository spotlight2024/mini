"""
WebDriver管理器 - 统一管理Driver生命周期
"""
import json
import time
import logging
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.file_detector import LocalFileDetector

from hybrid_driver.api.models import ConnectConfig
from hybrid_driver.log_config import get_logger
from stealthenium import stealth


logger = get_logger(__name__)


class WebDriverManager:
    """WebDriver管理器 - 统一管理Driver生命周期"""
    
    def __init__(self, session_id: str, site_config: Dict[str, Any], user_id: str):
        self.session_id = session_id
        self.site_config = site_config
        self.user_id = user_id
        self.driver = None
        self.page_manager = None
        self.chrome_options = None  # 存储chrome选项，可被外部修改
        self.logger = get_logger(f"WebDriverManager-{user_id}-{session_id}")
        self._sanitized_user_id = self._sanitize_identifier(user_id)
        self._cdp_endpoint: Optional[str] = None

    def _sanitize_identifier(self, value: str) -> str:
        """确保ID可安全用于文件路径或日志"""
        import re

        return re.sub(r"[^0-9A-Za-z._-]", "_", value)
    
    def create_driver(self) -> webdriver.Remote:
        """创建WebDriver"""
        self.logger.info("开始创建WebDriver...")
        
        # 创建ConnectConfig
        config = ConnectConfig(
            serial_id=f"session_{self.session_id}",
            user_id=str(self.user_id),
            webdriver_mode=self.site_config.get('webdriver_mode', 'remote'),
            remote_url=self.site_config.get('hub_url'),
            browser_version=self.site_config.get('browser_version', '138'),
            platform_name=self.site_config.get('platform_name', 'linux'),
            # android_package=self.site_config.get('android_package', 'com.tencent.mm'),
            # android_process=self.site_config.get('android_process', 'com.tencent.mm:appbrand0')
        )
        
        # 如果还没有Chrome选项，则创建默认配置
        if self.chrome_options is None:
            self.chrome_options = self._create_chrome_options()
        
        # 创建WebDriver
        self.driver = webdriver.Remote(
            command_executor=self.site_config['hub_url'],
            options=self.chrome_options
        )
        capabilities_json = json.dumps(
            self.chrome_options.to_capabilities(), ensure_ascii=False, indent=2
        )
        self.logger.info("gongcong111 stealthenium: {}", capabilities_json)

        try:
            caps = getattr(self.driver, "capabilities", {}) or {}
            self._cdp_endpoint = caps.get("se:cdp")
            if self._cdp_endpoint:
                self.logger.info("Captured CDP endpoint: %s", self._cdp_endpoint)
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Unable to read CDP endpoint: %s", exc)

        stealth(
            self.driver,
            languages=["zh-CN", "zh", "en", "ja", "zh-TW"],
            vendor="Google Inc.",
            platform="Linux x86_64",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        # 设置超时
        self.driver.set_page_load_timeout(self.site_config.get('page_load_timeout', 30))
        self.driver.implicitly_wait(self.site_config.get('implicit_wait', 10))
        self.driver.file_detector = LocalFileDetector()
        
        # 创建页面管理器
        from hybrid_driver.business_framework.core.page_manager import PageManager
        self.page_manager = PageManager(self.driver, self.session_id)
        
        self.logger.info("WebDriver创建成功")
        return self.driver
    
    def _create_chrome_options(self) -> Options:
        """创建Chrome选项"""
        chrome_options = Options()
        
        # 基础配置
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        # chrome_options.add_argument('--headless')
        
        # 用户数据目录
        user_data_dir = (
            f"/opt/chrome_user_data/chrome/session_{self._sanitized_user_id}/{self.site_config['site_name']}"
        )
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        
        # 性能优化
        performance_args = [
            '--disable-images', '--disable-plugins', '--disable-extensions',
            '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows', '--disable-ipc-flooding-protection',
            '--aggressive-cache-discard', '--memory-pressure-off'
        ]
        
        # 网络优化
        network_args = [
            '--max-connections-per-host=6', '--disable-background-networking'
        ]
        
        # SSL配置
        ssl_args = [
            '--ignore-certificate-errors', '--ignore-ssl-errors',
            '--ignore-certificate-errors-spki-list', '--disable-web-security'
        ]
        
        for arg in performance_args + network_args + ssl_args:
            chrome_options.add_argument(arg)
        
        chrome_options.add_argument('--page-load-strategy=eager')
        chrome_options.page_load_strategy = 'eager'
        
        return chrome_options
    
    def prepare_chrome_options(self) -> Options:
        """准备Chrome选项（基于默认配置），返回options对象供外部修改"""
        if self.chrome_options is None:
            self.chrome_options = self._create_chrome_options()
        return self.chrome_options
    
    def quit(self):
        """关闭WebDriver"""
        if self.driver:
            self.logger.info("关闭WebDriver")
            self.driver.quit()
            self.driver = None

    def get_cdp_endpoint(self) -> Optional[str]:
        """返回 Selenium 会话暴露的 CDP endpoint（若 Selenium Grid 支持）"""
        return self._cdp_endpoint
