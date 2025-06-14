import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AppiumExecutor:
    def __init__(self, appium_server_url, capabilities):
        options = UiAutomator2Options()
        for k, v in capabilities.items():
            options.set_capability(k, v)
        self.driver = webdriver.Remote(
            command_executor=appium_server_url,
            options=options
        )

    def wait_for_context(self, context_name_part, timeout=20):
        for _ in range(timeout * 2):
            contexts = self.driver.contexts
            print(contexts)
            print(self.driver.page_source)
            for ctx in contexts:
                if context_name_part in ctx:
                    self.driver.switch_to.context(ctx)
                    for handle in self.driver.window_handles:
                        self.driver.switch_to.window(handle)
                        print(handle,self.driver.title)
                    print(f"[AppiumExecutor] 切换到 context: {ctx}")
                    return ctx
            time.sleep(0.5)

        raise Exception(f"未找到 context 包含: {context_name_part}")

    def find_element(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def input_text(self, by, value, text, timeout=10):
        el = self.find_element(by, value, timeout)
        el.click()
        el.clear()
        el.send_keys(text)
        print(f"[AppiumExecutor] 输入文本: {text}")

    def quit(self):
        self.driver.quit()

if __name__ == "__main__":
    capabilities = {
        "platformName": "Android",
        "deviceName": "172.16.1.125:6521",
        "appPackage": "com.tencent.mm",
        "appActivity": "com.tencent.mm/.plugin.appbrand.ui.AppBrandUI00",
        "noReset": True,
        "unicodeKeyboard": True,
        "resetKeyboard": True,
        "chromeOptions": {
            "androidProcess": "com.tencent.mm:appbrand0"
        },
        "autoGrantPermissions": True,
        "chromedriverExecutable": "/Users/gongcong/.wdm/drivers/chromedriver/mac64/134.0.6998.136/chromedriver-mac-arm64/chromedriver"
    }
    appium_server_url = "http://localhost:4723"

    executor = AppiumExecutor(appium_server_url, capabilities)
    try:
        executor.wait_for_context('WEBVIEW')
        executor.input_text(By.CSS_SELECTOR, 'input[type=\"text\"]', '拿铁')
    finally:
        executor.quit()