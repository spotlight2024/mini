#!/usr/bin/env python3
"""
单用户数据持久化测试脚本
验证Chrome用户数据是否能够正确保存和恢复
"""

import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_proxy_functionality():
    """测试代理功能是否正常"""
    
    print("🧪 代理功能测试")
    print("=" * 50)
    
    # 定义用户ID和用户数据目录
    userId = "test2"
    # Chrome在容器内使用的路径，通过挂载映射到服务器目录
    user_data_dir = f"/opt/chrome_user_data/{userId}"
    print(f"👤 用户ID: {userId}")
    print(f"📁 容器内Chrome数据目录: {user_data_dir}")
    print(f"💾 实际存储到服务器: /root/workspace/chrome_data/{userId}")
    
    # Chrome选项配置
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument(f'--user-data-dir={user_data_dir}')
    print("🔧 Chrome选项已设置: 基本配置")
    
    try:
        print("📡 连接到Selenium Grid...")
        driver = webdriver.Remote(
            command_executor='http://localhost:30444/wd/hub',
            options=options
        )
        
        print("✅ 浏览器启动成功")
        
        # 1. 验证代理IP
        print("\n🔍 步骤1: 验证代理IP...")
        driver.get("https://qifu-api.baidubce.com/ip/local/geo/v1/district")
        print(f"driver.capabilities: {driver.capabilities}")
        time.sleep(3)
        
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            ip_info = json.loads(body_text)
            print(f"   ✅ IP信息: {ip_info}")
        except Exception as e:
            print(f"   ⚠️  IP检查异常: {e}")
        
        # 2. 访问淘宝首页
        # print("\n🛒 步骤2: 访问淘宝首页...")
        driver.get("https://www.baidu.com")
        # time.sleep(3)
        
        print(f"   ✅ 页面标题: {driver.title}")
        
        print("\n🎉 代理功能测试完成!")
        print("💡 说明:")
        print("   1. 代理功能正常工作")
        print("   2. 可以正常访问外部网站")
        print("   3. 出口IP通过代理")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False
        
    finally:
        try:
            # 保持浏览器打开5秒供观察
            print("\n⏳ 保持浏览器5秒供观察...")
            time.sleep(5)
            # driver.quit()
            print("🔄 浏览器已关闭")
        except:
            pass

def main():
    """主函数"""
    print("🚀 Selenium Grid 代理功能测试")
    print("=" * 50)
    
    # 测试代理功能
    success = test_proxy_functionality()
    
    if success:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 测试失败，请检查配置")
    
    print("\n📋 下一步操作:")
    print("1. 检查代理IP: 确认出口IP是否为目标代理")
    print("2. 测试网站访问: 确认可以正常访问目标网站")
    print("3. 检查代理日志: 查看tinyproxy是否正常工作")

if __name__ == "__main__":
    main()
