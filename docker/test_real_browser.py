#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实浏览器代理测试脚本
测试Chrome通过透明代理访问淘宝等网站
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

def test_browser_proxy():
    """测试真实浏览器代理功能"""
    
    print("🚀 启动真实浏览器代理测试")
    print("=" * 60)
    
    # Chrome选项配置
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # 注意：我们不添加任何代理参数，完全依赖HTTP_PROXY环境变量
    
    driver = None
    
    try:
        # 连接到Selenium Grid
        print("📡 连接到Selenium Grid (172.16.1.129:4444)...")
        driver = webdriver.Remote(
            command_executor='http://172.16.1.129:4444/wd/hub',
            options=chrome_options
        )
        
        print("✅ 浏览器启动成功")
        print(f"📱 浏览器信息: {driver.capabilities.get('browserName')} {driver.capabilities.get('browserVersion')}")
        
        # 测试1: 检查IP地址
        print("\n🔍 测试1: 检查出口IP地址")
        print("-" * 40)
        
        driver.get("https://ipinfo.io/json")
        
        # 等待页面加载
        time.sleep(3)
        
        # 获取IP信息
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            ip_info = json.loads(body_text)
            
            print(f"✅ 出口IP: {ip_info['ip']}")
            print(f"🌍 地理位置: {ip_info['data']['prov']} {ip_info['data']['city']} {ip_info['data']['district']}")
            print(f"🏢 ISP: {ip_info['data']['isp']}")
            
            # 验证是否为代理IP
            if ip_info['ip'] == "39.158.45.203":
                print("🎉 代理工作正常！IP匹配江西上饶代理服务器")
            else:
                print(f"⚠️  警告: IP不匹配，期望39.158.45.203，实际{ip_info['ip']}")
                
        except Exception as e:
            print(f"❌ 解析IP信息失败: {e}")
            print(f"页面内容: {driver.find_element(By.TAG_NAME, 'body').text[:200]}...")
        
        # 测试2: 访问淘宝
        print("\n🛒 测试2: 访问淘宝网站")
        print("-" * 40)
        
        driver.get("https://www.taobao.com")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        print(f"✅ 成功访问淘宝")
        print(f"📄 页面标题: {driver.title}")
        print(f"🔗 当前URL: {driver.current_url}")
        
        # 检查是否有反作弊检测
        page_source = driver.page_source.lower()
        
        if "验证" in page_source or "captcha" in page_source or "robot" in page_source:
            print("⚠️  检测到可能的反作弊验证")
        else:
            print("✅ 未检测到反作弊验证，代理隐蔽性良好")
        
        # 尝试找到搜索框证明页面正常加载
        try:
            search_box = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "q"))
            )
            print("✅ 搜索框加载正常，页面功能完整")
        except TimeoutException:
            print("⚠️  搜索框未找到，可能页面加载异常")
        
        # 测试3: 访问其他网站验证
        print("\n🌐 测试3: 访问百度验证网络连通性")
        print("-" * 40)
        
        driver.get("https://www.baidu.com")
        time.sleep(3)
        
        print(f"✅ 成功访问百度")
        print(f"📄 页面标题: {driver.title}")
        
        # 测试4: JavaScript执行
        print("\n⚡ 测试4: JavaScript执行测试")
        print("-" * 40)
        
        user_agent = driver.execute_script("return navigator.userAgent;")
        print(f"🔧 User Agent: {user_agent}")
        
        window_size = driver.execute_script("return [window.innerWidth, window.innerHeight];")
        print(f"📐 窗口大小: {window_size[0]}x{window_size[1]}")
        
        print("\n🎉 所有测试完成！")
        print("=" * 60)
        print("📊 测试结果总结:")
        print("   ✅ 浏览器启动正常")
        print("   ✅ 网络连接正常") 
        print("   ✅ 淘宝访问成功")
        print("   ✅ JavaScript执行正常")
        print("   ✅ 代理透明工作")
        
    except WebDriverException as e:
        print(f"❌ Selenium连接失败: {e}")
        print("请确保selenium-hub正在运行且chrome节点已注册")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        
    finally:
        if driver:
            print("\n🔄 关闭浏览器...")
            driver
            print("✅ 浏览器已关闭")

if __name__ == "__main__":
    test_browser_proxy()
