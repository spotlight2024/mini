#!/usr/bin/env python3
"""
运行豆包业务示例 - 直接通过 DoubaoBusiness 打开豆包首页
"""
import os
import sys

from loguru import logger


def _prepare_sys_path():
    """确保可以直接运行脚本"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    hybrid_driver_dir = os.path.dirname(current_dir)
    if hybrid_driver_dir not in sys.path:
        sys.path.insert(0, hybrid_driver_dir)

    mini_root_dir = os.path.dirname(hybrid_driver_dir)
    if mini_root_dir not in sys.path:
        sys.path.insert(0, mini_root_dir)


def main():
    """示例入口"""
    from hybrid_driver.business_framework.business.doubao_business import DoubaoBusiness

    session_id = "doubao_session_cli"
    user_id = "cli_user"

    doubao_business = DoubaoBusiness(session_id, user_id)

    try:
        doubao_business.initialize()
        doubao_business.initialize_pages()
        if doubao_business.open_home_page():
            print("✅ 成功打开豆包首页")
        else:
            print("❌ 打开豆包首页失败")
    finally:
        # print("finish")
        doubao_business.cleanup()


if __name__ == "__main__":
    _prepare_sys_path()
    main()
