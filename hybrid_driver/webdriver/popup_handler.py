import logging
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class PopupHandler:
    """弹窗处理器"""
    
    def __init__(self):
        self._popup_patterns = [
            {
                "type": "css",
                "selector": ".wx-popup-pannel",
                "action": "close"
            },
            {
                "type": "css",
                "selector": ".popup-close",
                "action": "click"
            }
        ]
    
    def handle_popups(self, driver: webdriver.Chrome) -> None:
        """处理所有可能的弹窗"""
        for pattern in self._popup_patterns:
            try:
                if pattern["type"] == "css":
                    element = driver.find_element(By.CSS_SELECTOR, pattern["selector"])
                    if element.is_displayed():
                        if pattern["action"] == "close":
                            self._close_popup(driver, element)
                        elif pattern["action"] == "click":
                            element.click()
            except (NoSuchElementException, TimeoutException):
                continue
            except Exception as e:
                logging.error(f"Error handling popup: {e}")
    
    def _close_popup(self, driver: webdriver.Chrome, popup_element: Any) -> None:
        """关闭弹窗"""
        try:
            # 尝试点击关闭按钮
            close_buttons = popup_element.find_elements(By.CSS_SELECTOR, ".close-btn, .popup-close")
            if close_buttons:
                close_buttons[0].click()
                return
            
            # 如果没有关闭按钮，尝试点击弹窗外部区域
            driver.execute_script("arguments[0].style.display = 'none';", popup_element)
        except Exception as e:
            logging.error(f"Error closing popup: {e}")
    
    def add_popup_pattern(self, pattern: Dict[str, str]) -> None:
        """添加新的弹窗模式"""
        self._popup_patterns.append(pattern)
    
    def remove_popup_pattern(self, selector: str) -> None:
        """移除弹窗模式"""
        self._popup_patterns = [p for p in self._popup_patterns if p["selector"] != selector] 