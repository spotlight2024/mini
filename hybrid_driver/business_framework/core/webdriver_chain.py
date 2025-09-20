"""
WebDriver链式调用封装类
"""
import time
import json
import logging
import subprocess
import requests
from typing import Optional, Union, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import wait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from hybrid_driver.log_config import get_logger


class WebDriverChain:
    """WebDriver链式调用封装类"""
    
    def __init__(self, driver: WebDriver, session_id: str):
        self.driver = driver
        self.session_id = session_id
        self.logger = get_logger(f"WebDriverChain-{session_id}")
    
    def log(self, message: str) -> 'WebDriverChain':
        """带时间戳的日志输出"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.logger.info(f"[{timestamp}] {message}")
        return self
    
    def navigate_to(self, url: str) -> 'WebDriverChain':
        """导航到指定URL"""
        self.log(f"🌐 开始打开 {url}")
        self.driver.get(url)
        return self
    
    def check_ip_info(self) -> 'WebDriverChain':
        """检查IP信息"""
        
        # 尝试多个IP检测服务
        ip_services = [
            'https://ipinfo.io/json',
            'https://ipapi.co/json',
            'http://ip-api.com/json'
        ]
        
        for service_url in ip_services:
            try:
                self.log(f"🌐 正在获取IP信息: {service_url}")
                
                # 方法1: 使用requests库
                try:
                    response = requests.get(service_url, timeout=10)
                    if response.status_code == 200:
                        ip_info = response.json()
                        self.log(f"📄 IP信息: {ip_info}")
                        return self
                except Exception as e:
                    self.log(f"⚠️ requests请求失败: {e}")
                
                # 方法2: 使用curl命令作为备用
                try:
                    result = subprocess.run(['curl', '-s', '--max-time', '10', service_url], 
                                          capture_output=True, text=True, timeout=15)
                    if result.returncode == 0 and result.stdout.strip():
                        ip_info = json.loads(result.stdout)
                        self.log(f"📄 IP信息: {ip_info}")
                        return self
                    else:
                        self.log(f"⚠️ curl命令失败: {result.stderr}")
                except Exception as e:
                    self.log(f"⚠️ curl执行失败: {e}")
                    
            except Exception as e:
                self.log(f"⚠️ IP检查异常 ({service_url}): {e}")
        
        self.log("❌ 所有IP检测方法都无法使用")
        return self
    
    def wait_for_element(self, by: Union[str, By], value: str, timeout: int = 10, description: str = "") -> Optional[WebElement]:
        """等待元素出现"""
        try:
            element = wait.WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            self.log(f"✅ 找到元素: {description or f'{by}={value}'}")
            return element
        except Exception as e:
            self.log(f"❌ 未找到元素 {description or f'{by}={value}'}: {e}")
            raise e
    
    def wait_for_clickable(self, by: Union[str, By], value: str, timeout: int = 10, description: str = "") -> Optional[WebElement]:
        """等待元素可点击"""
        try:
            element = wait.WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            self.log(f"✅ 元素可点击: {description or f'{by}={value}'}")
            return element
        except Exception as e:
            self.log(f"❌ 元素不可点击 {description or f'{by}={value}'}: {e}")
            raise e
    
    def click_element(self, by: Union[str, By], value: str, description: str = "") -> 'WebDriverChain':
        """点击元素"""
        element = self.wait_for_clickable(by, value, description=description)
        element.click()
        self.log(f"✅ 成功点击: {description or f'{by}={value}'}")
        return self
    
    def upload_file(self, by: Union[str, By], value: str, file_path: str, description: str = "") -> 'WebDriverChain':
        """上传文件"""
        element = self.wait_for_element(by, value, description=description)
        
        # 显示隐藏的file input
        self.log(f"🔧 显示隐藏的file input...")
        self.driver.execute_script("""
            arguments[0].style.display='block';
            arguments[0].style.visibility='visible';
            arguments[0].removeAttribute('disabled');
        """, element)
        
        # 上传文件
        self.log(f"📁 开始上传文件: {file_path}")
        element.send_keys(file_path)
        self.log(f"✅ 文件上传成功: {description or f'{by}={value}'}")
        return self
    
    def wait_and_click(self, by: Union[str, By], value: str, timeout: int = 15, description: str = "") -> 'WebDriverChain':
        """等待并点击元素"""
        element = self.wait_for_clickable(by, value, timeout, description)
        element.click()
        self.log(f"✅ 等待并点击成功: {description or f'{by}={value}'}")
        return self
    
    def wait_for_page_load(self, seconds: int = 5) -> 'WebDriverChain':
        """等待页面加载"""
        self.log(f"⏳ 等待页面加载 {seconds} 秒...")
        time.sleep(seconds)
        return self
    
    def get_page_info(self) -> 'WebDriverChain':
        """获取页面信息"""
        try:
            title = self.driver.title
            current_url = self.driver.current_url
            page_source_length = len(self.driver.page_source)
            
            self.log(f"📄 页面标题: {title}")
            self.log(f"🔗 当前URL: {current_url}")
            self.log(f"📊 页面源码长度: {page_source_length} 字符")
        except Exception as e:
            self.log(f"⚠️ 页面信息获取异常: {e}")
        return self
    
    def keep_alive(self, seconds: int = 90) -> 'WebDriverChain':
        """保持会话活跃"""
        self.log(f"⏳ 保持活跃 {seconds} 秒...")
        time.sleep(seconds)
        return self
    
    def quit(self) -> 'WebDriverChain':
        """关闭会话"""
        self.log("🔒 已关闭")
        self.driver.quit()
        return self
