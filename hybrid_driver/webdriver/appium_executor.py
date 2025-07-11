import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
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

    def test(self):
        contexts = self.driver.contexts
        element = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("菜单")')
        print(element.text)
        element.click()
        print(contexts)

    def wait_for_context(self, context_name_part, timeout=20):
        for _ in range(timeout * 2):
            contexts = self.driver.contexts
            element = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().text("菜单")')
            print(element.text)
            print(contexts)
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
    # 这些是您希望在哪个节点上运行测试的“要求”。
    # Selenium Grid 会将这些要求与注册上来节点（在 appium-node.toml 中定义）的
    # 能力(stereotype)进行匹配。
    capabilities = {
        "platformName": "Android",
        # 以下为 Appium 特有的 capabilities，推荐使用 'appium:' 前缀
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": "172.16.1.125:6556",
        "appium:appPackage": "com.tencent.mm",
        "appium:appActivity": "com.tencent.mm/.plugin.appbrand.ui.AppBrandUI00",
        "appium:noReset": True,
        "appium:unicodeKeyboard": True,
        "appium:resetKeyboard": True,
        "appium:autoGrantPermissions": True,
        "appium:chromeOptions": {
            "androidProcess": "com.tencent.mm:appbrand0"
        }
        # 不再需要硬编码 chromedriver 的路径
        # "chromedriverExecutable": "..."
    }

    # 将 command_executor 指向 Selenium Grid Hub 的地址
    # 您的所有请求都将发送到这里，由 Hub 负责分发
    appium_server_url = "http://localhost:4444"

    executor = AppiumExecutor(appium_server_url, capabilities)
    try:
        # executor.wait_for_context('WEBVIEW')
        # executor.input_text(By.CSS_SELECTOR, 'input[type=\"text\"]', '拿铁')
        executor.test()
    finally:
        executor.quit()