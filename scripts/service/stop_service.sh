#!/bin/bash

# 服务停止脚本
# 使用方法: ./shell/stop_service.sh

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$WORK_DIR/logs/service.pid"

echo "正在停止 Spot Light 服务..."

if [ ! -f "$PID_FILE" ]; then
    echo "未找到PID文件，服务可能未在运行"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "进程 $PID 不存在，服务可能已经停止"
    rm -f "$PID_FILE"
    exit 0
fi

echo "正在停止进程 $PID..."

# 尝试优雅停止
kill "$PID"

# 等待进程停止
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ 服务已成功停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 如果优雅停止失败，强制终止
echo "优雅停止失败，正在强制终止..."
kill -9 "$PID"

sleep 2

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ 服务已强制停止"
    rm -f "$PID_FILE"
else
    echo "❌ 无法停止服务，请手动检查进程 $PID"
    exit 1
fi 