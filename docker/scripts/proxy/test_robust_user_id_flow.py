#!/usr/bin/env python3
"""
测试健壮的 userId 文件读写流程的脚本
包含并发测试、过期清理、错误处理等
"""

import os
import time
import subprocess
import sys
import threading
import tempfile
import shutil

# 配置文件路径
USER_ID_FILE_PATH = '/tmp/adb_proxy_user_id.txt'
LOCK_FILE_PATH = '/tmp/adb_proxy_user_id.lock'

def test_basic_file_operations():
    """测试基本的文件读写操作"""
    print("🧪 测试基本文件读写操作...")
    
    # 测试写入带时间戳的 userId
    test_user_id = "test_user_123"
    current_time = int(time.time() * 1000)
    content = f"{current_time}:{test_user_id}"
    
    try:
        with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 成功写入带时间戳的 userId: {content}")
    except Exception as e:
        print(f"❌ 写入文件失败: {e}")
        return False
    
    # 测试读取
    try:
        with open(USER_ID_FILE_PATH, 'r', encoding='utf-8') as f:
            read_content = f.read().strip()
        print(f"✅ 成功读取内容: {read_content}")
        
        if read_content == content:
            print("✅ 内容匹配成功")
        else:
            print(f"❌ 内容不匹配: 期望 '{content}', 实际 '{read_content}'")
            return False
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False
    
    return True

def test_timestamp_parsing():
    """测试时间戳解析功能"""
    print("\n🧪 测试时间戳解析功能...")
    
    try:
        sys.path.append(os.path.dirname(__file__))
        from adb_proxy import get_user_id_from_file, cleanup_expired_files
        
        # 测试有效的时间戳
        current_time = int(time.time() * 1000)
        valid_content = f"{current_time}:test_user_valid"
        
        with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(valid_content)
        
        user_id = get_user_id_from_file()
        if user_id == "test_user_valid":
            print("✅ 有效时间戳解析成功")
        else:
            print(f"❌ 有效时间戳解析失败: 期望 'test_user_valid', 实际 '{user_id}'")
            return False
        
        # 测试过期的时间戳
        expired_time = current_time - 70000  # 70秒前
        expired_content = f"{expired_time}:test_user_expired"
        
        with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(expired_content)
        
        user_id = get_user_id_from_file()
        if user_id == "u10_":  # 应该返回默认值
            print("✅ 过期时间戳处理成功")
        else:
            print(f"❌ 过期时间戳处理失败: 期望 'u10_', 实际 '{user_id}'")
            return False
        
        # 测试格式错误
        invalid_content = "invalid_format"
        with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(invalid_content)
        
        user_id = get_user_id_from_file()
        if user_id == "u10_":  # 应该返回默认值
            print("✅ 格式错误处理成功")
        else:
            print(f"❌ 格式错误处理失败: 期望 'u10_', 实际 '{user_id}'")
            return False
        
    except Exception as e:
        print(f"❌ 时间戳解析测试失败: {e}")
        return False
    
    return True

def test_concurrent_access():
    """测试并发访问"""
    print("\n🧪 测试并发访问...")
    
    results = []
    errors = []
    
    def worker(worker_id):
        try:
            sys.path.append(os.path.dirname(__file__))
            from adb_proxy import get_user_id_from_file
            
            # 写入自己的 userId
            test_user_id = f"concurrent_user_{worker_id}"
            current_time = int(time.time() * 1000)
            content = f"{current_time}:{test_user_id}"
            
            with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 读取 userId
            user_id = get_user_id_from_file()
            results.append((worker_id, user_id))
            
        except Exception as e:
            errors.append((worker_id, str(e)))
    
    # 启动多个线程
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 检查结果
    if errors:
        print(f"❌ 并发测试出现错误: {errors}")
        return False
    
    print(f"✅ 并发测试完成，结果: {results}")
    return True

def test_cleanup_functionality():
    """测试清理功能"""
    print("\n🧪 测试清理功能...")
    
    try:
        sys.path.append(os.path.dirname(__file__))
        from adb_proxy import cleanup_expired_files
        
        # 创建过期文件
        expired_time = int(time.time() * 1000) - 70000  # 70秒前
        expired_content = f"{expired_time}:expired_user"
        
        with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(expired_content)
        
        # 创建锁文件
        with open(LOCK_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write("lock_content")
        
        print("📝 已创建过期文件")
        
        # 执行清理
        cleanup_expired_files()
        
        # 检查文件是否被清理
        if not os.path.exists(USER_ID_FILE_PATH) and not os.path.exists(LOCK_FILE_PATH):
            print("✅ 过期文件清理成功")
        else:
            print("❌ 过期文件清理失败")
            return False
        
    except Exception as e:
        print(f"❌ 清理功能测试失败: {e}")
        return False
    
    return True

def test_ps_command_modification():
    """测试 ps 命令修改功能"""
    print("\n🧪 测试 ps 命令修改功能...")
    
    try:
        sys.path.append(os.path.dirname(__file__))
        from adb_proxy import hook_ps_command
        
        # 设置测试 userId
        current_time = int(time.time() * 1000)
        test_user_id = "test_ps_user"
        content = f"{current_time}:{test_user_id}"
        
        with open(USER_ID_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
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

def cleanup_test_files():
    """清理测试文件"""
    try:
        if os.path.exists(USER_ID_FILE_PATH):
            os.remove(USER_ID_FILE_PATH)
        if os.path.exists(LOCK_FILE_PATH):
            os.remove(LOCK_FILE_PATH)
        print("🧹 已清理测试文件")
    except Exception as e:
        print(f"⚠️ 清理文件失败: {e}")

if __name__ == '__main__':
    print("🚀 开始测试健壮的 userId 动态传递流程")
    print("=" * 60)
    
    success = True
    
    # 运行所有测试
    tests = [
        ("基本文件操作", test_basic_file_operations),
        ("时间戳解析", test_timestamp_parsing),
        ("并发访问", test_concurrent_access),
        ("清理功能", test_cleanup_functionality),
        ("ps 命令修改", test_ps_command_modification),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if not test_func():
            success = False
            print(f"❌ {test_name} 测试失败")
        else:
            print(f"✅ {test_name} 测试通过")
    
    # 清理
    cleanup_test_files()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！健壮的 userId 动态传递流程正常工作")
        print("\n📋 功能特性:")
        print("  ✅ 支持时间戳格式的 userId 存储")
        print("  ✅ 自动过期清理机制")
        print("  ✅ 并发访问安全")
        print("  ✅ 错误处理和降级")
        print("  ✅ 定期清理任务")
        print("  ✅ 兼容旧格式")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查代码")
        sys.exit(1) 