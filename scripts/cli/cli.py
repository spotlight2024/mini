import argparse
import requests
import sys
import os

# 添加项目根目录到Python路径
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, SCRIPT_DIR)

from hybrid_driver.config.settings import settings

def main():
    parser = argparse.ArgumentParser(description="SpotLight CLI - 混合驱动服务命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # connect命令
    connect_parser = subparsers.add_parser("connect", help="连接设备")
    connect_parser.add_argument("--serial_id", required=True, help="设备序列号")
    connect_parser.add_argument("--ip", required=True, help="设备IP地址")
    connect_parser.add_argument("--port", type=int, required=True, help="设备端口")
    connect_parser.add_argument("--host", default=settings.API_HOST, help="API服务器地址")
    connect_parser.add_argument("--api_port", type=int, default=settings.API_PORT, help="API服务器端口")

    # action命令
    action_parser = subparsers.add_parser("action", help="执行操作")
    action_parser.add_argument("--serial_id", required=True, help="设备序列号")
    action_parser.add_argument("--type", required=True, help="操作类型")
    action_parser.add_argument("--params", default="{}", help="操作参数(JSON格式)")
    action_parser.add_argument("--host", default=settings.API_HOST, help="API服务器地址")
    action_parser.add_argument("--api_port", type=int, default=settings.API_PORT, help="API服务器端口")

    # find命令
    find_parser = subparsers.add_parser("find", help="查找元素")
    find_parser.add_argument("--serial_id", required=True, help="设备序列号")
    find_parser.add_argument("--selector", required=True, help="元素选择器")
    find_parser.add_argument("--host", default=settings.API_HOST, help="API服务器地址")
    find_parser.add_argument("--api_port", type=int, default=settings.API_PORT, help="API服务器端口")

    # status命令
    status_parser = subparsers.add_parser("status", help="查看服务状态")
    status_parser.add_argument("--host", default=settings.API_HOST, help="API服务器地址")
    status_parser.add_argument("--api_port", type=int, default=settings.API_PORT, help="API服务器端口")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 构建API基础URL
    base_url = f"http://{args.host}:{args.api_port}"

    try:
        if args.command == "connect":
            resp = requests.post(f"{base_url}/connect", json={
                "serial_id": args.serial_id,
                "ip": args.ip,
                "port": args.port
            })
            print(f"连接结果: {resp.json()}")
            
        elif args.command == "action":
            import json
            params = json.loads(args.params)
            resp = requests.post(f"{base_url}/action", json={
                "serial_id": args.serial_id,
                "type": args.type,
                "params": params
            })
            print(f"操作结果: {resp.json()}")
            
        elif args.command == "find":
            resp = requests.post(f"{base_url}/findElement", json={
                "serial_id": args.serial_id,
                "selector": args.selector
            })
            print(f"查找结果: {resp.json()}")
            
        elif args.command == "status":
            try:
                resp = requests.get(f"{base_url}/health")
                print(f"服务状态: {resp.json()}")
            except requests.exceptions.ConnectionError:
                print("❌ 无法连接到服务，请检查服务是否正在运行")
                sys.exit(1)
                
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到API服务器: {base_url}")
        print("请确保服务正在运行")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行命令时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 