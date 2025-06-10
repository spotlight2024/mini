import threading
from typing import Optional
from selenium.webdriver.chrome.webdriver import WebDriver
import adbutils
import logging
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By


from log_config import setup_logging

setup_logging()

BY_MAP = {
    "id": By.ID,
    "xpath": By.XPATH,
    "css selector": By.CSS_SELECTOR,
    "name": By.NAME,
    "class name": By.CLASS_NAME,
    "tag name": By.TAG_NAME,
    "link text": By.LINK_TEXT,
    "partial link text": By.PARTIAL_LINK_TEXT,
}

class AndroidDevice:
    def __init__(self, serial_id: str, ip: str = None, port: int = None):
        self.serial_id = serial_id
        self.ip = ip
        self.port = port
        self.driver: Optional[WebDriver] = None
        self.status = "disconnected"  # connected/disconnected

    def connect(self):
        try:
            logging.info(f"[AndroidDevice] 尝试通过 adb 查找设备 serial_id={self.serial_id}")
            device = adbutils.adb.device(serial=self.serial_id)
            if not device:
                logging.error(f"[AndroidDevice] adb 未找到设备 serial_id={self.serial_id}")
                self.status = "disconnected"
                return False
            logging.info(f"[AndroidDevice] adb 设备已找到 serial_id={self.serial_id}")

            # 初始化 WebDriver
            from web_driver import SeleniumWebDriver
            logging.info(f"[AndroidDevice] 准备初始化 WebDriver，serial_id={self.serial_id}")
            self.driver = SeleniumWebDriver().connect(self.serial_id)
            if not self.driver:
                logging.error(f"[AndroidDevice] WebDriver 初始化失败 serial_id={self.serial_id}")
                self.status = "disconnected"
                return False
            logging.info(f"[AndroidDevice] WebDriver 初始化成功 serial_id={self.serial_id}")
            self.status = "connected"
            return True
        except Exception as e:
            logging.exception(f"[AndroidDevice] 连接设备 serial_id={self.serial_id} 发生异常: {e}")
            self.status = "disconnected"
            return False

    def disconnect(self):
        if self.driver:
            try:
                logging.info(f"[AndroidDevice] 关闭 WebDriver serial_id={self.serial_id}")
                self.driver.quit()
            except Exception as e:
                logging.error(f"[AndroidDevice] 关闭 WebDriver 发生异常 serial_id={self.serial_id}: {e}")
            self.driver = None
        self.status = "disconnected"

    def is_alive(self):
        try:
            device = adbutils.adb.device(serial=self.serial_id)
            alive = device is not None
            logging.info(f"[AndroidDevice] 检查设备存活 serial_id={self.serial_id}, alive={alive}")
            return alive
        except Exception as e:
            logging.error(f"[AndroidDevice] 检查设备存活异常 serial_id={self.serial_id}: {e}")
            return False

    def do_action(self, action_type, params):
        if not self.driver:
            raise RuntimeError("WebDriver not connected")
        logging.info(f"[AndroidDevice] 执行操作 action_type={action_type}, params={params}, serial_id={self.serial_id}")
        if action_type == "click":
            selector = params.get("selector")
            elem = self.driver.find_element_by_css_selector(selector)
            elem.click()
            return True
        # 可扩展更多操作
        return None

    def find_element(self, method, selector) -> WebElement:
        """
        查找元素。
        参数 method 必须为以下字符串之一（与 Selenium By 枚举一一对应）：
            "id"               -> By.ID
            "xpath"            -> By.XPATH
            "css selector"     -> By.CSS_SELECTOR
            "name"             -> By.NAME
            "class name"       -> By.CLASS_NAME
            "tag name"         -> By.TAG_NAME
            "link text"        -> By.LINK_TEXT
            "partial link text"-> By.PARTIAL_LINK_TEXT
        selector 为具体的定位表达式。
        例如：
            method="css selector", selector=".my-class"
            method="xpath", selector="//div[@id='main']"
        """
        if not self.driver:
            raise RuntimeError("WebDriver not connected")
        by = BY_MAP.get(method.lower())
        if not by:
            raise ValueError(f"不支持的查找方式: {method}")
        logging.info(f"[AndroidDevice] 查找元素 method={method}, selector={selector}, serial_id={self.serial_id}")
        return self.driver.find_element(by, selector)


class DevicePool:
    def __init__(self):
        self.pool = {}  # serial_id -> AndroidDevice
        self.lock = threading.Lock()

    def connect(self, serial_id, ip=None, port=None) -> AndroidDevice:
        with self.lock:
            logging.info(f"[DevicePool] 尝试连接 serial_id={serial_id}, ip={ip}, port={port}")
            device = self.pool.get(serial_id)
            if device is None or not device.is_alive():
                device = AndroidDevice(serial_id, ip, port)
                if device.connect():
                    self.pool[serial_id] = device
                    logging.info(f"[DevicePool] 设备连接成功 serial_id={serial_id}")
                else:
                    logging.error(f"[DevicePool] 设备连接失败 serial_id={serial_id}")
                    raise RuntimeError(f"Failed to connect device {serial_id}")
            else:
                logging.info(f"[DevicePool] 设备已存在且存活 serial_id={serial_id}")
            return device

    def get(self, serial_id) -> Optional[AndroidDevice]:
        with self.lock:
            logging.info(f"[DevicePool] 获取设备 serial_id={serial_id}")
            return self.pool.get(serial_id)

    def disconnect(self, serial_id):
        with self.lock:
            logging.info(f"[DevicePool] 断开设备 serial_id={serial_id}")
            device = self.pool.pop(serial_id, None)
            if device:
                device.disconnect()


if __name__ == "__main__":
    DevicePool().connect("JJGICIN7QOAELNGI")
