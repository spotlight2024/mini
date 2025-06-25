#!/bin/bash

# 便捷启动脚本
# 使用方法: ./start.sh [命令]
# 命令可以是: start, stop, status, restart, logs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHELL_DIR="$SCRIPT_DIR/shell"

# 显示帮助信息
show_help() {
    echo "Spot Light 服务管理工具"
    echo ""
    echo "使用方法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动服务"
    echo "  stop      停止服务"
    echo "  status    查看服务状态"
    echo "  restart   重启服务"
    echo "  logs      查看日志 (等同于 logs -f)"
    echo "  logs -f   实时跟踪日志"
    echo "  logs -l   查看最新日志"
    echo "  logs -e   查看错误日志"
    echo "  logs -t   查看今天的日志"
    echo "  logs -a   查看所有日志文件"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start           # 启动服务"
    echo "  $0 status          # 查看状态"
    echo "  $0 logs -f         # 实时跟踪日志"
    echo "  $0 stop            # 停止服务"
}

# 检查shell目录是否存在
if [ ! -d "$SHELL_DIR" ]; then
    echo "❌ 错误: shell目录不存在: $SHELL_DIR"
    exit 1
fi

# 检查脚本是否存在
check_script() {
    local script_name="$1"
    if [ ! -f "$SHELL_DIR/$script_name" ]; then
        echo "❌ 错误: 脚本不存在: $SHELL_DIR/$script_name"
        exit 1
    fi
}

# 执行命令
case "$1" in
    start)
        check_script "start_service.sh"
        echo "🚀 启动 Spot Light 服务..."
        "$SHELL_DIR/start_service.sh"
        ;;
    stop)
        check_script "stop_service.sh"
        echo "🛑 停止 Spot Light 服务..."
        "$SHELL_DIR/stop_service.sh"
        ;;
    status)
        check_script "status.sh"
        "$SHELL_DIR/status.sh"
        ;;
    restart)
        check_script "restart_service.sh"
        echo "🔄 重启 Spot Light 服务..."
        "$SHELL_DIR/restart_service.sh"
        ;;
    logs)
        check_script "view_logs.sh"
        if [ -z "$2" ]; then
            # 默认实时跟踪日志
            "$SHELL_DIR/view_logs.sh" -f
        else
            # 传递所有参数给日志脚本
            shift
            "$SHELL_DIR/view_logs.sh" "$@"
        fi
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