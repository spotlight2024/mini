import logging
import sys
import pytest
from unittest.mock import patch, MagicMock
from webdriver.web_driver import SeleniumWebDriver
from selenium.common.exceptions import WebDriverException
import adbutils
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_connect_success():
    driver = SeleniumWebDriver()
    with patch("webdriver.web_driver.webdriver.Chrome") as mock_chrome:
        mock_instance = MagicMock()
        mock_chrome.return_value = mock_instance

        result = driver.connect("test_serial", "127.0.0.1", 9222)
        assert result is True
        assert "test_serial" in driver.sessions
        assert driver.sessions["test_serial"] == mock_instance

def test_connect_fail():
    driver = SeleniumWebDriver()
    with patch("webdriver.web_driver.webdriver.Chrome", side_effect=WebDriverException("fail")):
        result = driver.connect("test_serial", "127.0.0.1", 9222)
        assert result is False
        assert "test_serial" not in driver.sessions

# 真实连接测试（需本地有可用的 Chrome/Chromium 并开启了 9222 端口）
def test_real_connect():
    def get_target_ids(driver):
        targets = driver.execute_cdp_cmd("Target.getTargets", {})
        return {t['targetId'] for t in targets['targetInfos']}

    driver = SeleniumWebDriver()
    devices = adbutils.adb.device_list()
    logging.info(f"start connect")
    for device in devices:
        logging.info(f"device serial: ${device.serial}")
        logging.info(f"device info: ${device.app_current()}")
        result = driver.connect(device.serial)
        logging.info(f"connect result: ${result}")
        chrome_driver = driver.get_driver(device.serial)
        chrome_driver.implicitly_wait(2) 
        logging.info(f"has_html_modal: ${chrome_driver.find_element(By.CLASS_NAME, 'locationDialog shop-dialog--locationDialog')}")          
            

