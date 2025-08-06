#!/usr/bin/env python3
"""
代理功能测试脚本

测试Chrome代理插件在普通Web页面上的功能，验证代理IP是否生效。
"""

import sys
import os
import time
import logging

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)


def test_web_proxy():
    """测试Web代理功能"""
    logger.info("开始测试Web代理功能")
    
    # 配置Chrome选项
    options = ChromeOptions()
    
    # 反检测选项
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置User-Agent（桌面版Chrome）
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
    
    # 设置浏览器选项
    options.set_capability("browserName", "chrome")
    options.set_capability("browserVersion", "128.0")
    options.set_capability("platformName", "linux")
    
    logger.info(f"Chrome选项配置: {options.to_capabilities()}")
    
    driver = None
    try:
        # 连接到远程WebDriver
        remote_url = "http://172.16.1.129:4444/wd/hub"
        logger.info(f"连接到RemoteWebDriver: {remote_url}")
        
        driver = webdriver.Remote(
            command_executor=remote_url,
            options=options
        )
        
        logger.info("WebDriver创建成功")
        
        # 1. 测试访问IP检查服务
        logger.info("🔍 检查当前IP地址...")
        driver.get("https://httpbin.org/ip")
        time.sleep(3)
        
        ip_info = driver.find_element(By.TAG_NAME, "body").text
        logger.info(f"当前IP信息: {ip_info}")
        
        # 检查是否使用了代理IP
        proxy_ip = "61.132.231.167"  # 配置的代理IP
        if proxy_ip in ip_info:
            logger.info("✅ 成功检测到代理IP！")
        else:
            logger.warning("⚠️ 未检测到代理IP，可能代理未生效")
        
        # 2. 测试访问淘宝
        logger.info("🛒 测试访问淘宝...")
        driver.get("https://item.taobao.com/item.htm?ak=34793004&ali_trackid=2%3Amm_6856443298_3119000471_115756650058%3A1754475284667_557809130_0&bxsign=tbk68TT6YCJlsL2t3DK-cIeRSkPsUXbu_ZKZL-8ZBkD6BzxnJ2q0kMwtuNippNGXUzpPOHyXWAdak86fWQJOLo3IhDWaVwAOA6TlY2ppTUfHl6t-HAcHLQOKKiHmu06QWt54lgWMV_80E3TYGeowrxCMq462rziwSV2zUXOX55oYMMQSiIYEftVetXk8iVNvlcF&fromUld=1&id=918254347190&scm=20140767.59990_33_61_47_45_468_1754475276604.1%7Citem%7C918254347190.0&spm=a2e0b.27129982.d1654593950518.i1&union_lens=lensId%3AOPT%401754462579%40210489aa_0e0a_1987e1e6a52_40f1%40026hvVXNot6qsvwztVXA723Y%40eyJmbG9vcklkIjo4NTAwNywiic3JjRmxvb3JJZCI6IjgwMzA5In0ie%3Brecoveryid%3A201_33.102.137.153_34125663_1754475276261%3Bprepvid%3A201_33.102.137.153_34125663_1754475276261")
        time.sleep(5)
        
        current_url = driver.current_url
        title = driver.title
        logger.info(f"淘宝访问结果 - URL: {current_url}")
        logger.info(f"淘宝访问结果 - Title: {title}")
        
        # 检查是否成功访问
        if "淘宝" in title or "taobao" in current_url.lower():
            logger.info("✅ 成功访问淘宝，代理工作正常！")
        else:
            logger.warning("⚠️ 可能被重定向或阻止访问")
    
        return {
            "success": True,
            "ip_info": ip_info,
            "taobao_url": current_url,
            "taobao_title": title,
            "user_agent": ua_info,
            "ipinfo": ipinfo_text,
            "ipapi": ipapi_text
        }
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if driver:
            driver
            logger.info("WebDriver已清理")


def test_proxy_with_selenium_executor():
    """使用selenium_executor测试代理功能"""
    logger.info("使用selenium_executor测试代理功能")
    
    try:
        from hybrid_driver.webdriver.selenium_executor import test_proxy_connection
        from hybrid_driver.api.models import ConnectConfig
        
        # 创建配置
        config = ConnectConfig(
            serial_id="172.16.1.125:6569",
            user_id="0",
            webdriver_mode="remote",
            remote_url="http://172.16.1.129:4444/wd/hub",
            browser_version="128.0"
        )
        
        # 运行测试
        driver = test_proxy_connection()
        
        if driver:
            logger.info("✅ selenium_executor代理测试成功")
            return True
        else:
            logger.error("❌ selenium_executor代理测试失败")
            return False
            
    except Exception as e:
        logger.error(f"selenium_executor测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🌐 开始测试Web代理功能...")
    print("=" * 60)
    
    try:
        # 测试1: 直接使用Selenium
        print("📋 测试1: 直接使用Selenium")
        result1 = test_web_proxy()
        
        if result1["success"]:
            print("✅ 直接Selenium测试成功完成！")
            print()
            print("📊 测试结果:")
            print(f"   IP信息: {result1.get('ip_info', 'N/A')}")
            print(f"   淘宝URL: {result1.get('taobao_url', 'N/A')}")
            print(f"   淘宝标题: {result1.get('taobao_title', 'N/A')}")
            print(f"   User-Agent: {result1.get('user_agent', 'N/A')}")
            print(f"   IPInfo: {result1.get('ipinfo', 'N/A')}")
            print(f"   IP-API: {result1.get('ipapi', 'N/A')}")
            
            # 判断代理是否生效
            proxy_ip = "61.132.231.167"
            ip_info = result1.get('ip_info', '')
            if proxy_ip in ip_info:
                print("🎉 代理配置生效！使用的是代理出口IP")
            else:
                print("⚠️ 代理可能未生效，请检查配置")
        else:
            print(f"❌ 直接Selenium测试失败: {result1.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 60)
        
        # 测试2: 使用selenium_executor
        print("📋 测试2: 使用selenium_executor")
        # result2 = test_proxy_with_selenium_executor()
        
        # if result2:
        #     print("✅ selenium_executor测试成功")
        # else:
        #     print("❌ selenium_executor测试失败")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        return 130
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        logger.exception("测试过程中发生异常")
        return 1


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    exit_code = main()
    sys.exit(exit_code)
