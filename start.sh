#!/bin/bash

# SpotLight 项目主启动脚本
# 使用方法: ./start.sh [命令]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$SCRIPT_DIR/scripts/service"

# 显示帮助信息
show_help() {
    echo "SpotLight 项目主启动脚本"
    echo ""
    echo "使用方法: $0 [命令] [选项]"
    echo ""
    echo "服务管理命令:"
    echo "  start     启动服务"
    echo "  stop      停止服务"
    echo "  status    查看服务状态"
    echo "  restart   重启服务"
    echo "  logs      查看日志"
    echo ""
    echo "开发工具命令:"
    echo "  cli       运行CLI工具"
    echo "  test      运行测试"
    echo "  test-proxy 测试代理功能"
    echo "  test-docker-proxy 测试Docker代理方案"
    echo "  install   安装依赖"
    echo "  clean     清理缓存"
    echo ""
    echo "日志命令选项:"
    echo "  logs -f   实时跟踪日志"
    echo "  logs -e   查看错误日志"
    echo "  logs -t   查看今天的日志"
    echo "  logs -a   查看所有日志文件"
    echo ""
    echo "示例:"
    echo "  $0 start           # 启动服务"
    echo "  $0 status          # 查看状态"
    echo "  $0 cli status      # 使用CLI查看状态"
    echo "  $0 test            # 运行所有测试"
    echo "  $0 logs -f         # 实时跟踪日志"
}

# 检查服务脚本目录
if [ ! -d "$SERVICE_DIR" ]; then
    echo "❌ 错误: 服务脚本目录不存在: $SERVICE_DIR"
    exit 1
fi

# 执行命令
case "$1" in
    start)
        echo "🚀 启动 SpotLight 服务..."
        "$SERVICE_DIR/start_service.sh" "${@:2}"
        ;;
    stop)
        echo "🛑 停止 SpotLight 服务..."
        "$SERVICE_DIR/stop_service.sh" "${@:2}"
        ;;
    status)
        echo "📊 查看服务状态..."
        "$SERVICE_DIR/status.sh" "${@:2}"
        ;;
    restart)
        echo "🔄 重启 SpotLight 服务..."
        "$SERVICE_DIR/restart_service.sh" "${@:2}"
        ;;
    logs)
        echo "📝 查看日志..."
        "$SERVICE_DIR/view_logs.sh" "${@:2}"
        ;;
    cli)
        echo "🖥️  运行CLI工具..."
        python3 "$SCRIPT_DIR/scripts/cli/cli.py" "${@:2}"
        ;;
    test)
        echo "🧪 运行测试..."
        cd "$SCRIPT_DIR"
        python3 -m pytest tests/ -v
        ;;
    test-proxy)
        echo "🔗 测试代理功能..."
        cd "$SCRIPT_DIR"
        python3 scripts/test_proxy.py
        ;;
    test-docker-proxy)
        echo "🐳 测试Docker代理方案..."
        cd "$SCRIPT_DIR/docker"
        ./test_proxy_docker.sh
        ;;
    install)
        echo "📦 安装依赖..."
        if [ -d "$SCRIPT_DIR/.venv" ]; then
            source "$SCRIPT_DIR/.venv/bin/activate"
        fi
        pip install -r "$SCRIPT_DIR/requirements/requirements.txt"
        ;;
    clean)
        echo "🧹 清理缓存..."
        find "$SCRIPT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find "$SCRIPT_DIR" -type d -name "*.pyc" -delete 2>/dev/null || true
        find "$SCRIPT_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
        echo "✅ 缓存清理完成"
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        echo "❌ 错误: 请指定命令"
        echo ""
        show_help
        exit 1
        ;;
    *)
        echo "❌ 错误: 未知命令 '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac 