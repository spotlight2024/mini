"""
ActionChains包装器 - 支持链式调用和复杂交互
"""
from cgitb import reset
import time
import logging
from typing import Optional, Union, List, Tuple, Any
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from hybrid_driver.log_config import get_logger
from hybrid_driver.business_framework.core.human_actions import HumanMouse


class ActionChainsWrapper:
    """ActionChains包装器，支持链式调用"""
    
    def __init__(
        self,
        driver: WebDriver,
        session_id: str,
        human_mouse: Optional[HumanMouse] = None,
    ):
        self.driver = driver
        self.session_id = session_id
        self.actions = ActionChains(driver)
        self.logger = get_logger(f"ActionChains-{session_id}")
        self._human_mouse = human_mouse if human_mouse and human_mouse.enabled else None
        self._human_enabled = self._human_mouse is not None
        self._operation_log: list[str] = []
        self._flow_start: Optional[float] = None

    def log(self, message: str) -> 'ActionChainsWrapper':
        """带时间戳的日志输出"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.logger.info(f"[ActionChains] {message}")
        return self

    def _record_action(self, action: str, detail: str = "") -> None:
        if self._flow_start is None:
            self._flow_start = time.perf_counter()
        entry = f"{action}({detail})" if detail else action
        self._operation_log.append(entry)
        self.logger.debug(
            f"[ActionChains] queued {entry} human={'on' if self._human_enabled and self._human_mouse else 'off'}"
        )

    def enable_human_actions(self) -> 'ActionChainsWrapper':
        """启用人类化行为"""
        if self._human_mouse and self._human_mouse.enabled:
            self._human_enabled = True
            self.log("✅ 已启用人类化鼠标行为")
        else:
            self.log("⚠️ 未配置人类化鼠标，保持原生行为")
        return self

    def disable_human_actions(self) -> 'ActionChainsWrapper':
        """关闭人类化行为"""
        self._human_enabled = False
        self.log("✅ 已关闭人类化鼠标行为")
        return self
    
    def move_to_element(self, by: Union[str, By], value: str, description: str = "") -> 'ActionChainsWrapper':
        """移动到元素"""
        element = self.driver.find_element(by, value)
        detail = description or f"{by}={value}"
        if self._human_enabled and self._human_mouse:
            self._human_mouse.move_to(element, detail)
        else:
            self.actions.move_to_element(element)
        self._record_action("move", detail)
        return self
    
    def click(self, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """点击操作"""
        if by and value:
            element = self.driver.find_element(by, value)
            detail = description or f"{by}={value}"
            if self._human_enabled and self._human_mouse:
                self._human_mouse.click(element, detail)
            else:
                self.actions.click(element)
            self._record_action("click", detail)
        else:
            if self._human_enabled:
                self.log("🖱️ 人类化点击当前位置暂未实现，使用原生点击")
            self.actions.click()
            self._record_action("click", "current_position")
        return self
    
    def double_click(self, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """双击操作"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.double_click(element)
            self._record_action("double_click", description or f"{by}={value}")
        else:
            self.actions.double_click()
            self._record_action("double_click", "current_position")
        return self
    
    def right_click(self, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """右键点击"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.context_click(element)
            self._record_action("right_click", description or f"{by}={value}")
        else:
            self.actions.context_click()
            self._record_action("right_click", "current_position")
        return self
    
    def drag_and_drop(self, source_by: Union[str, By], source_value: str, 
                     target_by: Union[str, By], target_value: str, description: str = "") -> 'ActionChainsWrapper':
        """拖拽操作"""
        source = self.driver.find_element(source_by, source_value)
        target = self.driver.find_element(target_by, target_value)
        self.actions.drag_and_drop(source, target)
        detail = description or f"{source_by}={source_value} -> {target_by}={target_value}"
        self._record_action("drag_and_drop", detail)
        return self
    
    def send_keys(self, keys: str, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """发送按键"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.send_keys_to_element(element, keys)
            self._record_action("send_keys", description or f"{by}={value}")
        else:
            self.actions.send_keys(keys)
            self._record_action("send_keys", keys)
        return self
    
    def key_down(self, key: str, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """按下按键"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.key_down(key, element)
            self._record_action("key_down", f"{key}@{description or f'{by}={value}'}")
        else:
            self.actions.key_down(key)
            self._record_action("key_down", key)
        return self
    
    def key_up(self, key: str, by: Optional[Union[str, By]] = None, value: Optional[str] = None, description: str = "") -> 'ActionChainsWrapper':
        """释放按键"""
        if by and value:
            element = self.driver.find_element(by, value)
            self.actions.key_up(key, element)
            self._record_action("key_up", f"{key}@{description or f'{by}={value}'}")
        else:
            self.actions.key_up(key)
            self._record_action("key_up", key)
        return self
    
    def hover(self, by: Union[str, By], value: str, description: str = "") -> 'ActionChainsWrapper':
        """悬停操作"""
        element = self.driver.find_element(by, value)
        self.actions.move_to_element(element)
        self._record_action("hover", description or f"{by}={value}")
        return self
    
    def scroll_to_element(self, by: Union[str, By], value: str, description: str = "") -> 'ActionChainsWrapper':
        """滚动到元素"""
        element = self.driver.find_element(by, value)
        self.actions.move_to_element(element)
        self._record_action("scroll_to", description or f"{by}={value}")
        return self
    
    def perform(self) -> 'ActionChainsWrapper':
        """执行所有动作"""
        has_native_actions = False
        w3c_actions = getattr(self.actions, "w3c_actions", None)
        if w3c_actions and getattr(w3c_actions, "devices", None):
            has_native_actions = any(getattr(device, "actions", None) for device in w3c_actions.devices)
        if has_native_actions:
            self.actions.perform()
        elapsed_ms = 0.0
        if self._flow_start is not None:
            elapsed_ms = (time.perf_counter() - self._flow_start) * 1000
        summary = " -> ".join(self._operation_log) if self._operation_log else "no actions queued"
        human_flag = "on" if self._human_enabled and self._human_mouse else "off"
        self.logger.info(
            f"[ActionChains] perform human={human_flag} ops={summary} elapsed={elapsed_ms:.1f}ms"
        )
        self.reset_actions(log=False)
        return self

    def reset_actions(self, log: bool = True) -> 'ActionChainsWrapper':
        """重置动作链"""
        self.actions = ActionChains(self.driver)
        self._operation_log.clear()
        self._flow_start = None
        if log:
            self.logger.debug("[ActionChains] reset action chain")
        return self
    
    def click_and_wait_for_new_page(self, by: Union[str, By], value: str, page_name: str = "search_results", description: str = "") -> 'ActionChainsWrapper':
        """点击元素并等待新页面"""
        element = self.driver.find_element(by, value)
        
        # 记录当前窗口数量
        current_windows = len(self.driver.window_handles)
        
        # 点击元素
        self.actions.move_to_element(element).click().perform()
        self.logger.info(f"[ActionChains] click-and-wait target={description or f'{by}={value}'}")
        
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
