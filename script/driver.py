from typing import Dict, Any
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from abc import ABC, abstractmethod

class BaseDriver(ABC):
    @abstractmethod
    def connect(self, serial_id: str) -> bool:
        pass

    @abstractmethod
    def action(self, serial_id: str, id: str, action_type: str, params: dict) -> dict:
        pass

    @abstractmethod
    def find_element(self, serial_id: str, selector: str) -> dict:
        pass
