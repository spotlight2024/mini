#!/bin/bash

# SpotLight 服务启动脚本
# 使用方法: ./start_service.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
HYBRID_DRIVER_DIR="$PROJECT_ROOT/hybrid_driver"

# 显示帮助信息
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

# 检查项目目录
if [ ! -d "$HYBRID_DRIVER_DIR" ]; then
    echo "❌ 错误: hybrid_driver目录不存在: $HYBRID_DRIVER_DIR"
    exit 1
fi

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3"
    exit 1
fi

# 检查虚拟环境
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "🔧 激活虚拟环境..."
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# 检查依赖
echo "📦 检查依赖..."
cd "$HYBRID_DRIVER_DIR"
if [ ! -f "requirements.txt" ]; then
    echo "⚠️  警告: 未找到requirements.txt，尝试使用项目根目录的requirements.txt"
    if [ -f "$PROJECT_ROOT/requirements/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements/requirements.txt"
    fi
else
    pip install -r requirements.txt
fi

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"

# 启动服务
echo "🚀 启动 SpotLight 服务..."
echo "📍 项目根目录: $PROJECT_ROOT"
echo "📍 服务目录: $HYBRID_DRIVER_DIR"
echo "📍 日志目录: $PROJECT_ROOT/logs"

cd "$HYBRID_DRIVER_DIR"
python3 main.py 