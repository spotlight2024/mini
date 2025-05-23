import pytest
from unittest.mock import patch, MagicMock
from webdriver.web_driver import SeleniumWebDriver
from selenium.common.exceptions import WebDriverException

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
    driver = SeleniumWebDriver()
    result = driver.connect("real_test", "172.16.1.125", 6520)
    assert result is True
    assert "real_test" in driver.sessions
    wd = driver.sessions["real_test"]
    # 只要能访问属性说明连接成功
    assert wd.title is not None
    wd.quit() 