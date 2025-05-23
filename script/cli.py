import argparse
import requests

def main():
    parser = argparse.ArgumentParser(description="Spotium CLI")
    subparsers = parser.add_subparsers(dest="command")

    connect_parser = subparsers.add_parser("connect")
    connect_parser.add_argument("--serial_id", required=True)
    connect_parser.add_argument("--ip", required=True)
    connect_parser.add_argument("--port", type=int, required=True)

    action_parser = subparsers.add_parser("action")
    action_parser.add_argument("--serial_id", required=True)
    action_parser.add_argument("--type", required=True)
    action_parser.add_argument("--params", default="{}")

    find_parser = subparsers.add_parser("find")
    find_parser.add_argument("--serial_id", required=True)
    find_parser.add_argument("--selector", required=True)

    args = parser.parse_args()

    if args.command == "connect":
        resp = requests.post("http://localhost:8000/connect", json={
            "serial_id": args.serial_id,
            "ip": args.ip,
            "port": args.port
        })
        print(resp.json())
    elif args.command == "action":
        import json
        params = json.loads(args.params)
        resp = requests.post("http://localhost:8000/action", json={
            "serial_id": args.serial_id,
            "type": args.type,
            "params": params
        })
        print(resp.json())
    elif args.command == "find":
        resp = requests.post("http://localhost:8000/findElement", json={
            "serial_id": args.serial_id,
            "selector": args.selector
        })
        print(resp.json())
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 