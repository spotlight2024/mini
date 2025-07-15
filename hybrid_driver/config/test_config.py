#!/usr/bin/env python3
"""
配置系统测试脚本
"""
import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid_driver.config.settings import Settings


def test_config_loading():
    """测试配置加载"""
    print("=" * 50)
    print("测试配置加载")
    print("=" * 50)
    
    settings = Settings()
    
    # 测试基本配置项
    print(f"API主机: {settings.API_HOST}")
    print(f"API端口: {settings.API_PORT}")
    print(f"日志级别: {settings.LOG_LEVEL}")
    print(f"WebDriver模式: {settings.WEBDRIVER_MODE}")
    print(f"线程池大小: {settings.THREAD_POOL_MAX_WORKERS}")
    
    return True


def test_config_validation():
    """测试配置验证"""
    print("\n" + "=" * 50)
    print("测试配置验证")
    print("=" * 50)
    
    settings = Settings()
    
    # 验证配置
    is_valid = settings.validate_config()
    print(f"配置验证结果: {'通过' if is_valid else '失败'}")
    
    return is_valid


def test_config_export():
    """测试配置导出"""
    print("\n" + "=" * 50)
    print("测试配置导出")
    print("=" * 50)
    
    settings = Settings()
    
    # 导出配置
    config_data = settings.get_config()
    
    # 保存到临时文件
    temp_file = "temp_config.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    print(f"配置已导出到: {temp_file}")
    
    # 读取并验证
    with open(temp_file, 'r', encoding='utf-8') as f:
        loaded_config = json.load(f)
    
    print(f"导出的配置项数量: {len(loaded_config)}")
    print(f"API配置: {loaded_config.get('api', {})}")
    
    # 清理临时文件
    os.remove(temp_file)
    
    return True


def test_environment_variables():
    """测试环境变量配置"""
    print("\n" + "=" * 50)
    print("测试环境变量配置")
    print("=" * 50)
    
    # 设置测试环境变量
    test_vars = {
        "API_PORT": "9999",
        "LOG_LEVEL": "DEBUG",
        "THREAD_POOL_MAX_WORKERS": "50"
    }
    
    # 保存原始环境变量
    original_vars = {}
    for key in test_vars:
        original_vars[key] = os.environ.get(key)
        os.environ[key] = test_vars[key]
    
    try:
        # 重新创建Settings实例以加载新的环境变量
        settings = Settings()
        
        print(f"API端口 (环境变量): {settings.API_PORT}")
        print(f"日志级别 (环境变量): {settings.LOG_LEVEL}")
        print(f"线程池大小 (环境变量): {settings.THREAD_POOL_MAX_WORKERS}")
        
        # 验证环境变量是否生效
        assert settings.API_PORT == 9999, f"API端口应该为9999，实际为{settings.API_PORT}"
        assert settings.LOG_LEVEL == "DEBUG", f"日志级别应该为DEBUG，实际为{settings.LOG_LEVEL}"
        assert settings.THREAD_POOL_MAX_WORKERS == 50, f"线程池大小应该为50，实际为{settings.THREAD_POOL_MAX_WORKERS}"
        
        print("✅ 环境变量配置测试通过")
        return True
        
    finally:
        # 恢复原始环境变量
        for key, value in original_vars.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)


def test_config_file():
    """测试配置文件"""
    print("\n" + "=" * 50)
    print("测试配置文件")
    print("=" * 50)
    
    # 创建测试配置文件
    test_config = {
        "api": {
            "port": 8888,
            "title": "测试API"
        },
        "logging": {
            "level": "WARNING"
        },
        "thread_pool": {
            "max_workers": 25
        }
    }
    
    test_file = "test_config.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, indent=2, ensure_ascii=False)
    
    try:
        # 测试从文件加载配置
        settings = Settings()
        settings.load_from_file(test_file)
        
        print(f"API端口 (配置文件): {settings.API_PORT}")
        print(f"API标题 (配置文件): {settings.API_TITLE}")
        print(f"日志级别 (配置文件): {settings.LOG_LEVEL}")
        print(f"线程池大小 (配置文件): {settings.THREAD_POOL_MAX_WORKERS}")
        
        # 验证配置文件是否生效
        assert settings.API_PORT == 8888, f"API端口应该为8888，实际为{settings.API_PORT}"
        assert settings.API_TITLE == "测试API", f"API标题应该为'测试API'，实际为{settings.API_TITLE}"
        assert settings.LOG_LEVEL == "WARNING", f"日志级别应该为WARNING，实际为{settings.LOG_LEVEL}"
        assert settings.THREAD_POOL_MAX_WORKERS == 25, f"线程池大小应该为25，实际为{settings.THREAD_POOL_MAX_WORKERS}"
        
        print("✅ 配置文件测试通过")
        return True
        
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)


def main():
    """主测试函数"""
    print("开始配置系统测试...")
    
    tests = [
        ("配置加载", test_config_loading),
        ("配置验证", test_config_validation),
        ("配置导出", test_config_export),
        ("环境变量", test_environment_variables),
        ("配置文件", test_config_file)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 50)
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1


if __name__ == "__main__":
    exit(main()) 