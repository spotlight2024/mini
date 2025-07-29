#!/usr/bin/env python3
"""
测试 userId 文件读写流程的脚本
"""

import os
import time
import subprocess
import sys

# 配置文件路径
USER_ID_FILE_PATH = '/tmp/adb_proxy_user_id.txt'

def test_user_id_file_operations():
    """测试 userId 文件的读写操作"""
    print("🧪 开始测试 userId 文件读写流程...")
    
    # 测试 1: 写入 userId
    test_user_id = "test_user_123"
    print(f"📝 写入测试 userId: {test_user_id}")
    
    try:
        with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(test_user_id)
        print(f"✅ 成功写入文件: {USER_ID_FILE_PATH}")
    except Exception as e:
        print(f"❌ 写入文件失败: {e}")
        return False
    
    # 测试 2: 读取 userId
    print("📖 读取 userId 文件...")
    try:
        with open(USER_ID_FILE_PATH, 'r', encoding='utf-8') as f:
            read_user_id = f.read().strip()
        print(f"✅ 成功读取 userId: {read_user_id}")
        
        if read_user_id == test_user_id:
            print("✅ userId 匹配成功")
        else:
            print(f"❌ userId 不匹配: 期望 '{test_user_id}', 实际 '{read_user_id}'")
            return False
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False
    
    # 测试 3: 模拟 ADB 代理读取
    print("🔍 模拟 ADB 代理读取 userId...")
    try:
        # 导入 ADB 代理的函数
        sys.path.append(os.path.dirname(__file__))
        from adb_proxy import get_user_id_from_file
        
        proxy_user_id = get_user_id_from_file()
        print(f"✅ ADB 代理读取到 userId: {proxy_user_id}")
        
        if proxy_user_id == test_user_id:
            print("✅ ADB 代理读取成功")
        else:
            print(f"❌ ADB 代理读取不匹配: 期望 '{test_user_id}', 实际 '{proxy_user_id}'")
            return False
    except Exception as e:
        print(f"❌ ADB 代理读取失败: {e}")
        return False
    
    # 测试 4: 测试默认值
    print("🔄 测试默认值（删除文件后）...")
    try:
        os.remove(USER_ID_FILE_PATH)
        print("🗑️ 已删除 userId 文件")
        
        proxy_user_id = get_user_id_from_file()
        print(f"✅ 默认 userId: {proxy_user_id}")
        
        if proxy_user_id == "u10_":
            print("✅ 默认值正确")
        else:
            print(f"❌ 默认值不正确: 期望 'u10_', 实际 '{proxy_user_id}'")
            return False
    except Exception as e:
        print(f"❌ 测试默认值失败: {e}")
        return False
    
    print("🎉 所有测试通过！")
    return True

def test_ps_command_modification():
    """测试 ps 命令修改功能"""
    print("\n🧪 测试 ps 命令修改功能...")
    
    # 模拟写入一个测试 userId
    test_user_id = "test_user_456"
    with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(test_user_id)
    
    try:
        from adb_proxy import hook_ps_command
        
        # 测试原始 ps 命令
        original_command = "0011shell:ps && ps -A"
        original_data = original_command.encode('utf-8')
        
        print(f"📝 原始命令: {original_command}")
        
        # 应用 hook
        modified_data = hook_ps_command(original_data)
        modified_command = modified_data.decode('utf-8')
        
        print(f"🔧 修改后命令: {modified_command}")
        
        # 检查是否包含正确的 grep 过滤
        expected_grep = f"grep '{test_user_id}'"
        if expected_grep in modified_command:
            print("✅ ps 命令修改成功")
            return True
        else:
            print(f"❌ ps 命令修改失败，未找到预期的 grep: {expected_grep}")
            return False
            
    except Exception as e:
        print(f"❌ ps 命令修改测试失败: {e}")
        return False

def cleanup():
    """清理测试文件"""
    try:
        if os.path.exists(USER_ID_FILE_PATH):
            os.remove(USER_ID_FILE_PATH)
            print("🧹 已清理测试文件")
    except Exception as e:
        print(f"⚠️ 清理文件失败: {e}")

if __name__ == '__main__':
    print("🚀 开始测试 userId 动态传递流程")
    print("=" * 50)
    
    success = True
    
    # 运行测试
    if not test_user_id_file_operations():
        success = False
    
    if not test_ps_command_modification():
        success = False
    
    # 清理
    cleanup()
    
    print("=" * 50)
    if success:
        print("🎉 所有测试通过！userId 动态传递流程正常工作")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查代码")
        sys.exit(1) 