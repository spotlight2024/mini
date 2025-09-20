#!/usr/bin/env python3
"""
极简代理验证脚本
用法：python3 verify.py
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def verify_proxy():
    """验证透明代理是否正常工作"""
    
    print("🔍 Selenium Chrome 透明代理验证")
    print("=" * 40)
    
    # 最简Chrome配置
    options = Options()
    
    try:
        # 连接Grid
        print("📡 连接 Selenium Grid...")
        driver = webdriver.Remote(
            command_executor='http://localhost:4444/wd/hub',
            options=options
        )
        
        print(f"✅ Chrome启动成功: {driver.capabilities['browserVersion']}")
        
        # 检查代理IP
        print("🌐 检查出口IP...")
        driver.get("https://ipinfo.io/json")
        time.sleep(2)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        ip_info = json.loads(body_text)
        
        ip = ip_info['ip']
        location = f"{ip_info['data']['prov']} {ip_info['data']['city']}"
        isp = ip_info['data']['isp']
        
        print(f"📍 出口IP: {ip}")
        print(f"🌍 地理位置: {location}")
        print(f"🏢 ISP: {isp}")
        
        # 验证是否为代理IP
        if ip == "39.158.45.203":
            print("🎉 代理工作正常！")
            status = "✅ PASS"
        else:
            print("⚠️  代理可能有问题")
            status = "❌ FAIL"
        
        # 快速测试网站访问
        print("🛒 测试网站访问...")
        driver.get("https://www.baidu.com")
        time.sleep(3)
        
        if "百度" in driver.title:
            print(f"✅ 网站访问正常: {driver.title}")
        else:
            print(f"⚠️  网站访问异常: {driver.title}")
        
        print("\n📊 验证结果:")
        print(f"   状态: {status}")
        print(f"   代理IP: {ip}")
        print(f"   位置: {location}")
        print("   Chrome: 无感知透明代理")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        
    finally:
        try:
            driver.quit()
            print("🔄 浏览器已关闭")
        except:
            pass

if __name__ == "__main__":
    verify_proxy()
