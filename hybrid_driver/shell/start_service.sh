#!/bin/bash

# 服务启动脚本
# 使用方法: ./shell/start_service.sh

# 设置工作目录（脚本在shell子目录中，需要回到上级目录）
WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WORK_DIR"

# 创建日志目录
mkdir -p logs

# 生成日志文件名（包含时间戳）
LOG_FILE="logs/service_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="logs/service.pid"

echo "正在启动 Spot Light 服务..."
echo "工作目录: $WORK_DIR"
echo "日志文件: $LOG_FILE"
echo "PID文件: $PID_FILE"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "服务已经在运行中 (PID: $PID)"
        echo "如需重启，请先运行: ./shell/stop_service.sh"
        exit 1
    else
        echo "发现过期的PID文件，正在清理..."
        rm -f "$PID_FILE"
    fi
fi

# 使用nohup启动服务
nohup python3 main.py > "$LOG_FILE" 2>&1 &

# 保存PID
echo $! > "$PID_FILE"

# 等待服务启动
sleep 3

# 检查服务是否成功启动
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "✅ 服务启动成功!"
    echo "PID: $(cat "$PID_FILE")"
    echo "日志文件: $LOG_FILE"
    echo ""
    echo "查看实时日志: tail -f $LOG_FILE"
    echo "停止服务: ./shell/stop_service.sh"
    echo "查看服务状态: ./shell/status.sh"
else
    echo "❌ 服务启动失败!"
    echo "请检查日志文件: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi 