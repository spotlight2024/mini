import logging
from dataclasses import dataclass
from typing import List, Dict, Any

import adbutils
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from log_config import setup_logging
from webdriver.selenium_executor import SeleniumWebExecutor

setup_logging()


def test_real_connect():
    driver = SeleniumWebExecutor()
    devices = adbutils.adb.device_list()
    logging.info(f"start connect")
    for device in devices:
        logging.info(f"device serial: ${device.serial}")
        logging.info(f"device info: ${device.app_current()}")
        result = driver.connect(device.serial)
        logging.info(f"connect result: ${result}")
        chrome_driver = driver.web_executor
        chrome_driver.implicitly_wait(3)

        # wait = WebDriverWait(chrome_driver, 10)  # 最长等待 10 秒
        # logging.info(f"current handle: ${chrome_driver.current_window_handle}")
        #
        # # 等待页面加载完成并获取可见页面
        # visible_pages = wait.until(PageVisibilityCondition(min_visible_pages=1))
        # logging.info(f"visible pages: {visible_pages}")
        #
        # chrome_driver.switch_to.window(visible_pages[0].handle)
        #
        # # logging.info(f"is popup : ${chrome_driver.find_element(By.CSS_SELECTOR,".wx-popup-pannel").is_displayed()}")
        # try_close_popup(chrome_driver, 3)


if __name__ == "__main__":
    test_real_connect()
