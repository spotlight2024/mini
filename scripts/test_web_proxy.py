#!/usr/bin/env python3
"""
测试 WebDriver 代理功能的脚本

用于验证 selenium_executor.py 的修复是否完整。
"""

import sys
import os

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_import():
    """测试模块导入是否正常"""
    try:
        from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor
        print("✅ 成功导入 SeleniumWebExecutor")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_web_executor_import():
    """测试 WebExecutor 导入"""
    try:
        from hybrid_driver.webdriver.web_executor import WebExecutor
        print("✅ 成功导入 WebExecutor")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_models_import():
    """测试模型导入"""
    try:
        from hybrid_driver.api.models import ConnectConfig, OperationItem
        print("✅ 成功导入 ConnectConfig 和 OperationItem")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_settings_import():
    """测试设置导入"""
    try:
        from hybrid_driver.config.settings import settings
        print("✅ 成功导入 settings")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_logger_import():
    """测试日志导入"""
    try:
        from hybrid_driver.log_config import get_logger
        print("✅ 成功导入 get_logger")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_webdriver_utils_import():
    """测试 WebDriver 工具导入"""
    try:
        from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils
        print("✅ 成功导入 WebDriverUtils")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 开始测试 WebDriver 模块导入...")
    print("=" * 50)
    
    tests = [
        test_import,
        test_web_executor_import,
        test_models_import,
        test_settings_import,
        test_logger_import,
        test_webdriver_utils_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！模块导入问题已修复。")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
