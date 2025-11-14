#!/usr/bin/env python3
"""
SpotLight Hybrid Driver API 服务器启动脚本
"""
import argparse
import os
import sys

import uvicorn

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hybrid_driver.config.settings import Settings
from hybrid_driver.server_optimized import app


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="启动SpotLight Hybrid Driver API服务器"
    )
    parser.add_argument("--host", default=Settings.API_HOST, help="服务器主机地址")
    parser.add_argument(
        "--port", type=int, default=Settings.API_PORT, help="服务器端口"
    )
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--reload", action="store_true", help="启用自动重载")

    args = parser.parse_args()

    print(f"启动SpotLight Hybrid Driver API服务器...")
    print(f"地址: http://{args.host}:{args.port}")
    print(f"文档: http://{args.host}:{args.port}/docs")
    print(f"调试模式: {args.debug}")
    print(f"自动重载: {args.reload}")
    print("-" * 50)

    try:
        uvicorn.run(
            "hybrid_driver.server_optimized:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level=Settings.LOG_LEVEL.lower(),
        )
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动服务器时发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
