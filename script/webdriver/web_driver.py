from webdriver.driver import BaseDriver
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from webdriver_manager.core.driver_cache import DriverCacheManager
from selenium.webdriver.chrome.service import Service as ChromeService
import logging
import os

TEST_CONFIG = {
    "chrome_version": "134.0.6998.136",
    "ip": "172.16.1.125",
    "port": 6520,
    "device_serial": "test_serial",
    "android_process": "com.tencent.mm:tools",
    "android_package": "com.tencent.mm",
    "android_activity": "com.google.android.apps.chrome.Main",
}


class SeleniumWebDriver(BaseDriver):
    def __init__(self):
        self.sessions = {}

    def connect(self, serial_id: str, ip: str, port: int) -> bool:
        try:
            logging.info(f"Connecting to WebDriver at {ip}:{port}")
            options = webdriver.ChromeOptions()

            options.enable_mobile(
                android_package=TEST_CONFIG["android_package"],
                android_activity=TEST_CONFIG["android_activity"],
                device_serial=TEST_CONFIG["device_serial"],
            )
            options.add_experimental_option("androidUseRunningApp", True)
            options.add_experimental_option("androidProcess", TEST_CONFIG["android_process"])


            path = find_chromedriver(ChromeDriverManager(driver_version=TEST_CONFIG["chrome_version"]).install())   
            
            logging.info(f"ChromeDriver path: {path}")
            
            service = ChromeService(executable_path=path)
            driver = webdriver.Chrome(options=options, service=service)

            driver.implicitly_wait(10)
            logging(f"WebDriver connected: {driver.page_source}")
            self.sessions[serial_id] = driver
            return True
        except WebDriverException as e:
            print(f"WebDriver connect error: {e}")
            return False

    def action(self, serial_id: str, action_type: str, params: dict) -> dict:
        driver = self.sessions.get(serial_id)
        if not driver:
            return {"code": "fail", "message": "No session found"}
        try:
            if action_type == "click":
                selector = params.get("selector")
                element = driver.find_element("css selector", selector)
                element.click()
                return {"code": "success", "message": "Clicked"}
            return {"code": "fail", "message": "Unknown action"}
        except Exception as e:
            return {"code": "fail", "message": str(e)}

    def find_element(self, serial_id: str, selector: str) -> dict:
        driver = self.sessions.get(serial_id)
        if not driver:
            return {"code": "fail", "message": "No session found"}
        try:
            element = driver.find_element("css selector", selector)
            return {
                "code": "success",
                "element": {"tag": element.tag_name, "text": element.text},
                "message": "Found",
            }
        except Exception as e:
            return {"code": "fail", "message": str(e)}

def find_chromedriver(path):
    # 如果 path 就是可执行文件且文件名正确，直接返回
    basename = os.path.basename(path)
    if (basename == "chromedriver" or basename == "chromedriver-mac-arm64") and os.path.isfile(path) and os.access(path, os.X_OK):
        return path
    # 否则在目录下查找
    for root, dirs, files in os.walk(path):
        for file in files:
            if file in ("chromedriver", "chromedriver-mac-arm64"):
                full_path = os.path.join(root, file)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    return full_path
    raise FileNotFoundError("No valid chromedriver executable found.")
# if __name__ == "__main__":
# driver = SeleniumWebDriver()
# driver.connect("1234567890", "127.0.0.1", 9222)
