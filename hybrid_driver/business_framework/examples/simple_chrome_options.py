#!/usr/bin/env python3
"""
简化的Chrome选项配置示例 - 直接操作chrome_options对象
"""
import sys
import os

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
hybrid_driver_dir = os.path.dirname(os.path.dirname(current_dir))
mini_root_dir = os.path.dirname(hybrid_driver_dir)
sys.path.insert(0, mini_root_dir)

from hybrid_driver.business_framework.business.taobao_business import TaobaoBusiness


def example_basic_usage():
    """基础使用示例 - 直接操作chrome_options"""
    print("🔧 示例1: 直接操作chrome_options对象")
    
    # 创建业务实例
    taobao_business = TaobaoBusiness("example_session_1")
    
    # 直接获取chrome_options对象
    chrome_options = taobao_business.get_chrome_options()
    
    # 直接添加你需要的参数
    chrome_options.add_argument("--proxy-server=http://proxy.example.com:8080")
    chrome_options.add_argument("--user-agent=CustomBot/1.0")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    print("✅ Chrome选项配置完成")
    # taobao_business.initialize()  # 使用配置好的选项创建driver


def example_conditional_config():
    """条件配置示例"""
    print("\n🔧 示例2: 根据条件配置")
    
    taobao_business = TaobaoBusiness("example_session_2")
    chrome_options = taobao_business.get_chrome_options()
    
    # 根据需要添加配置
    use_proxy = True
    enable_headless = False
    
    if use_proxy:
        chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:1080")
        print("🌐 配置代理")
    
    if enable_headless:
        chrome_options.add_argument("--headless")
        print("🔇 启用无头模式")
    
    # 其他常用配置
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    print("✅ 条件配置完成")


def main():
    """主函数"""
    print("🚀 简化的Chrome选项配置示例")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_conditional_config()
        
        print("\n💡 使用说明:")
        print("1. 创建业务实例后直接调用 get_chrome_options() 获取选项对象")
        print("2. 直接操作chrome_options对象，添加你需要的任何参数")
        print("3. 在调用 initialize() 之前完成所有配置")
        print("4. 所有配置都基于框架的默认优化设置")
        
    except Exception as e:
        print(f"❌ 运行示例时发生错误: {e}")


if __name__ == "__main__":
    main()


