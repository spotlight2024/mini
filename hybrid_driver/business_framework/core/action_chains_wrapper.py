"""
ActionChains包装器 - 支持链式调用和复杂交互
"""
import time
import logging
from typing import Optional, Union, List, Tuple, Any
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from hybrid_driver.log_config import get_logger


class ActionChainsWrapper:
    """ActionChains包装器，支持链式调用"""
    
    def __init__(self, driver: WebDriver, session_id: str):
        self.driver = driver
        self.session_id = session_id
        self.actions = ActionChains(driver)
        self.logger = get_logger(f"ActionChains-{session_id}")
    
    def log(self, message: str) -> 'ActionChainsWrapper':
        """带时间戳的日志输出"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.logger.info(f"[{timestamp}] {message}")
        return self
    
    def move_to_element(self, by: Union[str, By], value: str, description: str = "") -> 'ActionChainsWrapper':
        """移动到元素"""
        element = self.driver.find_element(by, value)
        self.actions.move_to_element(element)
        self.log(f"🖱️ 移动到元素: {description or f'{by}={value}'}")
        return self
    
    def click(self, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """点击操作"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.click(element)
            self.log(f"🖱️ 点击元素: {description or f'{by}={value}'}")
        else:
            self.actions.click()
            self.log(f"🖱️ 点击当前位置")
        return self
    
    def double_click(self, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """双击操作"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.double_click(element)
            self.log(f"🖱️ 双击元素: {description or f'{by}={value}'}")
        else:
            self.actions.double_click()
            self.log(f"🖱️ 双击当前位置")
        return self
    
    def right_click(self, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """右键点击"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.context_click(element)
            self.log(f"🖱️ 右键点击元素: {description or f'{by}={value}'}")
        else:
            self.actions.context_click()
            self.log(f"🖱️ 右键点击当前位置")
        return self
    
    def drag_and_drop(self, source_by: Union[str, By], source_value: str, 
                     target_by: Union[str, By], target_value: str, description: str = "") -> 'ActionChainsWrapper':
        """拖拽操作"""
        source = self.driver.find_element(source_by, source_value)
        target = self.driver.find_element(target_by, target_value)
        self.actions.drag_and_drop(source, target)
        self.log(f"🖱️ 拖拽操作: {description or f'{source_by}={source_value} -> {target_by}={target_value}'}")
        return self
    
    def send_keys(self, keys: str, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """发送按键"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.send_keys_to_element(element, keys)
            self.log(f"⌨️ 向元素发送按键: {description or f'{by}={value}'}")
        else:
            self.actions.send_keys(keys)
            self.log(f"⌨️ 发送按键: {keys}")
        return self
    
    def key_down(self, key: str, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """按下按键"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.key_down(key, element)
            self.log(f"⌨️ 按下按键: {key} on {description or f'{by}={value}'}")
        else:
            self.actions.key_down(key)
            self.log(f"⌨️ 按下按键: {key}")
        return self
    
    def key_up(self, key: str, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """释放按键"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.key_up(key, element)
            self.log(f"⌨️ 释放按键: {key} on {description or f'{by}={value}'}")
        else:
            self.actions.key_up(key)
            self.log(f"⌨️ 释放按键: {key}")
        return self
    
    def hover(self, by: Union[str, By], value: str, description: str = "") -> 'ActionChainsWrapper':
        """悬停操作"""
        element = self.driver.find_element(by, value)
        self.actions.move_to_element(element)
        self.log(f"🖱️ 悬停在元素: {description or f'{by}={value}'}")
        return self
    
    def scroll_to_element(self, by: Union[str, By], value: str, description: str = "") -> 'ActionChainsWrapper':
        """滚动到元素"""
        element = self.driver.find_element(by, value)
        self.actions.move_to_element(element)
        self.log(f"📜 滚动到元素: {description or f'{by}={value}'}")
        return self
    
    def perform(self) -> 'ActionChainsWrapper':
        """执行所有动作"""
        self.actions.perform()
        self.log("✅ 执行所有动作完成")
        return self
    
    def reset_actions(self) -> 'ActionChainsWrapper':
        """重置动作链"""
        self.actions = ActionChains(self.driver)
        self.log("🔄 重置动作链")
        return self
    
    def click_and_wait_for_new_page(self, by: Union[str, By], value: str, page_name: str = "search_results", description: str = "") -> 'ActionChainsWrapper':
        """点击元素并等待新页面"""
        element = self.driver.find_element(by, value)
        
        # 记录当前窗口数量
        current_windows = len(self.driver.window_handles)
        
        # 点击元素
        self.actions.move_to_element(element).click().perform()
        self.log(f"🖱️ 点击元素: {description or f'{by}={value}'}")
        
        # 等待新页面出现
        self.log(f"⏳ 等待新页面出现...")
        start_time = time.time()
        while time.time() - start_time < 10:
            if len(self.driver.window_handles) > current_windows:
                new_window = [w for w in self.driver.window_handles if w not in [self.driver.current_window_handle]][0]
                self.driver.switch_to.window(new_window)
                self.log(f"✅ 新页面已出现并切换: {page_name}")
                return self
            time.sleep(0.5)
        
        self.log("⚠️ 新页面未在指定时间内出现")
        return self
