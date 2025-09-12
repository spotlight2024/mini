#!/usr/bin/env python3
"""
运行测试脚本 - 测试新框架的功能
"""
import sys
import os

# 添加当前目录到Python路径，以便能找到business_framework包
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 添加hybrid_driver目录到Python路径，以便能找到log_config
hybrid_driver_dir = os.path.dirname(current_dir)
sys.path.insert(0, hybrid_driver_dir)

# 添加mini根目录到Python路径，以便能找到hybrid_driver包
mini_root_dir = os.path.dirname(hybrid_driver_dir)
sys.path.insert(0, mini_root_dir)

from tests.test_taobao_search import test_taobao_concurrent_with_actions


def main():
    """主函数"""
    print("🚀 开始测试业务框架...")
    print("=" * 50)
    
    try:
        # 运行淘宝搜索测试
        test_taobao_concurrent_with_actions(concurrent_count=1)
        print("✅ 测试完成")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
