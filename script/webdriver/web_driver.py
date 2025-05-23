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
    "chrome_version": "128.0.6613.88",
    "ip": "172.16.1.125",
    "port": 6520,
    "device_serial": "test_serial",
    "android_process": "org.chromium.webview_shell",
    "android_package": "org.chromium.webview_shell"
}


class SeleniumWebDriver(BaseDriver):
    def __init__(self):
        self.sessions = {}

    def connect(self, serial_id: str, ip: str, port: int) -> bool:
        try:
            logging.info(f"Connecting to WebDriver at {ip}:{port}")

            device_serial = f"{ip}:{port}"
            options = webdriver.ChromeOptions()

            options.enable_mobile(
                android_package=TEST_CONFIG["android_package"],
                device_serial=device_serial,
            )
            options.add_experimental_option("androidUseRunningApp", True)
            options.add_experimental_option("androidProcess", TEST_CONFIG["android_process"])

            logging.info("connect options: " + str(options.to_capabilities()))

            path = ChromeDriverManager(driver_version=TEST_CONFIG["chrome_version"]).install()   
            
            logging.info(f"ChromeDriver path: {path}")
            
            # 新版本chromedriver的文件名是THIRD_PARTY_NOTICES.chromedriver，需要替换为chromedriver
            if 'THIRD_PARTY_NOTICES.chromedriver' in path:
                path = path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
            
            service = Service(executable_path=path)
            driver = webdriver.Chrome(options=options, service=service)

            driver.implicitly_wait(10)
            logging.info(f"WebDriver connected: {driver.page_source}")
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
    logging.info(f"basename: {basename}, path: {path}")
    if (basename in ("chromedriver", "chromedriver-mac-arm64")) and os.path.isfile(path) and os.access(path, os.X_OK):
        return path
    # 否则在目录下查找
    for root, dirs, files in os.walk(path):
        for file in files:
            # 只认精确文件名，且排除任何包含 'THIRD_PARTY' 的文件
            if file in ("chromedriver", "chromedriver-mac-arm64") and "THIRD_PARTY" not in file:
                full_path = os.path.join(root, file)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    return full_path
    raise FileNotFoundError("No valid chromedriver executable found.")
# if __name__ == "__main__":
# driver = SeleniumWebDriver()
# driver.connect("1234567890", "127.0.0.1", 9222)
