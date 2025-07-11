#!/usr/bin/env python3
"""
ChromeDriver 节点功能测试脚本

测试场景:
1. 桌面 Chrome 浏览器测试
2. Android WebView 测试 (需要连接 Android 设备)
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Selenium Grid Hub 地址
GRID_URL = "http://localhost:4444/wd/hub"

def test_remote_chrome():
    """测试远程 Chrome 实例连接"""
    print("🔍 测试远程 Chrome 实例连接...")
    
    # 远程 Chrome 的 capabilities
    capabilities = {
        "browserName": "chrome",
        "platformName": "any", 
        "browserVersion": "128.0",
        "goog:chromeOptions": {
            "debuggerAddress": "host.docker.internal:9222",
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        }
    }
    
    driver = None
    try:
        driver = webdriver.Remote(
            command_executor=GRID_URL,
            desired_capabilities=capabilities
        )
        
        # 访问测试页面
        driver.get("https://www.google.com")
        print(f"✅ 页面标题: {driver.title}")
        
        # 搜索测试
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("ChromeDriver test")
        search_box.submit()
        
        # 等待搜索结果
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search"))
        )
        print("✅ 搜索功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 远程 Chrome 测试失败: {e}")
        print("💡 提示: 请确保远程 Chrome 实例已启动并开启调试端口 9222")
        return False
    finally:
        if driver:
            driver.quit()

def test_android_webview():
    """测试 Android WebView (需要连接 Android 设备)"""
    print("🔍 测试 Android WebView...")
    
    # Android WebView 的 capabilities
    capabilities = {
        "browserName": "chrome",
        "platformName": "android",
        "browserVersion": "128.0",
        "appium:automationName": "UiAutomator2",
        "appium:chromeOptions": {
            "androidPackage": "com.android.chrome",
            "androidUseRunningApp": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"]
        }
    }
    
    driver = None
    try:
        driver = webdriver.Remote(
            command_executor=GRID_URL,
            desired_capabilities=capabilities
        )
        
        # 访问测试页面
        driver.get("https://m.baidu.com")
        print(f"✅ 移动页面标题: {driver.title}")
        
        # 检查是否是移动版本
        if "百度" in driver.title:
            print("✅ 移动端 WebView 测试成功")
            return True
        else:
            print("⚠️  页面可能不是移动版本")
            return False
        
    except Exception as e:
        print(f"❌ Android WebView 测试失败: {e}")
        print("💡 提示: 请确保 Android 设备已连接并启用了开发者选项")
        return False
    finally:
        if driver:
            driver.quit()

def check_grid_status():
    """检查 Selenium Grid 状态"""
    print("🔍 检查 Selenium Grid 状态...")
    
    try:
        import requests
        response = requests.get("http://localhost:4444/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Grid 状态: 就绪")
            print(f"✅ 节点数量: {len(data.get('value', {}).get('nodes', []))}")
            return True
        else:
            print(f"❌ Grid 状态异常: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到 Grid: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 ChromeDriver 节点功能测试开始")
    print("=" * 50)
    
    # 检查 Grid 状态
    if not check_grid_status():
        print("❌ Selenium Grid 不可用，请先启动服务")
        return
    
    print()
    
    # 测试远程 Chrome
    remote_result = test_remote_chrome()
    print()
    
    # 测试 Android WebView
    android_result = test_android_webview()
    print()
    
    # 总结
    print("=" * 50)
    print("📊 测试结果总结:")
    print(f"远程 Chrome: {'✅ 通过' if remote_result else '❌ 失败'}")
    print(f"Android WebView: {'✅ 通过' if android_result else '❌ 失败'}")
    
    if remote_result and android_result:
        print("🎉 所有测试通过！ChromeDriver 节点工作正常")
    elif android_result:
        print("⚠️  Android 功能正常，远程 Chrome 功能需要检查连接")
    else:
        print("❌ 测试失败，请检查配置和服务状态")

if __name__ == "__main__":
    main() 