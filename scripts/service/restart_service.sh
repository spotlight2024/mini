#!/bin/bash

# 服务重启脚本
# 使用方法: ./shell/restart_service.sh

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "正在重启 Spot Light 服务..."

# 停止服务
if [ -f "$WORK_DIR/shell/stop_service.sh" ]; then
    echo "1. 停止现有服务..."
    "$WORK_DIR/shell/stop_service.sh"
    sleep 2
else
    echo "❌ 未找到 stop_service.sh 脚本"
    exit 1
fi

# 启动服务
if [ -f "$WORK_DIR/shell/start_service.sh" ]; then
    echo "2. 启动服务..."
    "$WORK_DIR/shell/start_service.sh"
else
    echo "❌ 未找到 start_service.sh 脚本"
    exit 1
fi

echo ""
echo "✅ 服务重启完成!"
echo "查看状态: ./shell/status.sh" 