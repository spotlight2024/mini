from webdriver.driver import BaseDriver
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

class SeleniumWebDriver(BaseDriver):
    def __init__(self):
        self.sessions = {}

    def connect(self, serial_id: str, ip: str, port: int) -> bool:
        try:
            options = webdriver.ChromeOptions()
            options.debugger_address = f"{ip}:{port}"
            driver = webdriver.Chrome(options=options)
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
            return {"code": "success", "element": {"tag": element.tag_name, "text": element.text}, "message": "Found"}
        except Exception as e:
            return {"code": "fail", "message": str(e)} 
        
if __name__ == "__main__":
    driver = SeleniumWebDriver()
    driver.connect("1234567890", "127.0.0.1", 9222)