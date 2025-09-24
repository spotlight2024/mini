#!/bin/bash

# SpotLight 服务启动脚本（Poetry 原生流程）
# 使用方法: ./start_service.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
HYBRID_DRIVER_DIR="$PROJECT_ROOT/hybrid_driver"
POETRY_BIN="${POETRY_BIN:-poetry}"

show_help() {
    echo "SpotLight 服务启动脚本"
    echo ""
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -d, --debug    调试模式"
    echo "  -p, --port     指定端口 (默认: 8002)"
    echo ""
    echo "示例:"
    echo "  $0              # 默认启动"
    echo "  $0 -d           # 调试模式"
    echo "  $0 -p 8003      # 指定端口"
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    show_help
    exit 0
fi

if [ ! -d "$HYBRID_DRIVER_DIR" ]; then
    echo "❌ 错误: hybrid_driver目录不存在: $HYBRID_DRIVER_DIR"
    exit 1
fi

if ! command -v "$POETRY_BIN" &> /dev/null; then
    echo "❌ 错误: 未检测到 Poetry，可通过 'pipx install poetry' 或官方脚本安装"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo "❌ 错误: 未找到 pyproject.toml，无法继续"
    exit 1
fi

echo "📦 使用 Poetry 安装依赖..."
cd "$PROJECT_ROOT"
"$POETRY_BIN" install --with dev --no-root --no-interaction

mkdir -p "$PROJECT_ROOT/logs"

echo "🚀 启动 SpotLight 服务..."
echo "📍 项目根目录: $PROJECT_ROOT"
echo "📍 服务目录: $HYBRID_DRIVER_DIR"
echo "📍 日志目录: $PROJECT_ROOT/logs"

cd "$HYBRID_DRIVER_DIR"
"$POETRY_BIN" run python main.py
