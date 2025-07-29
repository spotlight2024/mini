#!/usr/bin/env python3
"""
简化的 userId 文件读写流程测试脚本
"""

import os
import sys

# 配置文件路径
USER_ID_FILE_PATH = '/tmp/adb_proxy_user_id.txt'

def test_basic_flow():
    """测试基本的 userId 传递流程"""
    print("🧪 测试简化的 userId 传递流程...")
    
    try:
        sys.path.append(os.path.dirname(__file__))
        from adb_proxy import get_user_id_from_file, hook_ps_command
        
        # 测试 1: 写入有效 userId
        test_user_id = "test_user_123"
        print(f"📝 写入测试 userId: {test_user_id}")
        
        with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(test_user_id)
        
        # 测试 2: 读取 userId
        print("📖 读取 userId...")
        user_id = get_user_id_from_file()
        
        if user_id == test_user_id:
            print("✅ userId 读取成功")
        else:
            print(f"❌ userId 读取失败: 期望 '{test_user_id}', 实际 '{user_id}'")
            return False
        
        # 测试 3: ps 命令修改
        print("🔧 测试 ps 命令修改...")
        original_command = "0011shell:ps && ps -A"
        original_data = original_command.encode('utf-8')
        
        modified_data = hook_ps_command(original_data)
        modified_command = modified_data.decode('utf-8')
        
        expected_grep = f"grep '{test_user_id}'"
        if expected_grep in modified_command:
            print("✅ ps 命令修改成功")
        else:
            print(f"❌ ps 命令修改失败，未找到预期的 grep: {expected_grep}")
            return False
        
        # 测试 3.5: 空 userId 时不修改命令
        print("🔧 测试空 userId 时的 ps 命令...")
        with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write("")  # 写入空字符串
        
        modified_data = hook_ps_command(original_data)
        modified_command = modified_data.decode('utf-8')
        
        # 应该保持原始命令不变
        if modified_command == original_command:
            print("✅ 空 userId 时保持原始命令不变")
        else:
            print(f"❌ 空 userId 时命令被修改了: {modified_command}")
            return False
        
        # 测试 4: 删除文件后的默认值
        print("🔄 测试默认值...")
        os.remove(USER_ID_FILE_PATH)
        
        user_id = get_user_id_from_file()
        if user_id == "u10_":
            print("✅ 默认值正确")
        else:
            print(f"❌ 默认值错误: 期望 'u10_', 实际 '{user_id}'")
            return False
        
        # 测试 5: 默认值时不修改 ps 命令
        print("🔧 测试默认值时的 ps 命令...")
        original_command = "0011shell:ps && ps -A"
        original_data = original_command.encode('utf-8')
        
        modified_data = hook_ps_command(original_data)
        modified_command = modified_data.decode('utf-8')
        
        # 应该保持原始命令不变
        if modified_command == original_command:
            print("✅ 默认值时保持原始命令不变")
        else:
            print(f"❌ 默认值时命令被修改了: {modified_command}")
            return False
        
        print("🎉 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
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
    print("🚀 开始测试简化的 userId 传递流程")
    print("=" * 50)
    
    success = test_basic_flow()
    
    # 清理
    cleanup()
    
    print("=" * 50)
    if success:
        print("🎉 简化测试通过！userId 传递流程正常工作")
        sys.exit(0)
    else:
        print("❌ 测试失败，请检查代码")
        sys.exit(1) 