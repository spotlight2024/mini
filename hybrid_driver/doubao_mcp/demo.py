"""
命令行示例：直接调用 Playwright 自动化执行一次查询。
"""

from __future__ import annotations

import argparse
import json

from .config import DoubaoMCPConfig
from .doubao_playwright import DoubaoPlaywrightAutomation


def main() -> None:
    parser = argparse.ArgumentParser(description="Doubao MCP 查询演示")
    parser.add_argument("query", help="要输入豆包的查询内容")
    args = parser.parse_args()

    config = DoubaoMCPConfig.from_env()
        automation = DoubaoPlaywrightAutomation(config)
    try:
        result = automation.search(args.query)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    finally:
        automation.shutdown()


if __name__ == "__main__":
    main()
