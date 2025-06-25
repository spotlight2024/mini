#!/bin/bash

# 服务状态检查脚本
# 使用方法: ./shell/status.sh

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$WORK_DIR/logs/service.pid"

echo "=== Spot Light 服务状态 ==="
echo "工作目录: $WORK_DIR"

if [ ! -f "$PID_FILE" ]; then
    echo "状态: ❌ 未运行 (未找到PID文件)"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "状态: ❌ 未运行 (进程 $PID 不存在)"
    echo "清理过期的PID文件..."
    rm -f "$PID_FILE"
    exit 1
fi

echo "状态: ✅ 运行中"
echo "PID: $PID"
echo "启动时间: $(ps -o lstart= -p "$PID")"
echo "内存使用: $(ps -o rss= -p "$PID" | awk '{print $1/1024 " MB"}')"
echo "CPU使用: $(ps -o %cpu= -p "$PID")%"

# 检查端口是否在监听
if netstat -tlnp 2>/dev/null | grep -q ":8000.*$PID"; then
    echo "端口状态: ✅ 8000端口正在监听"
else
    echo "端口状态: ⚠️  8000端口未监听"
fi

# 显示最近的日志文件
echo ""
echo "=== 日志文件 ==="
if [ -d "$WORK_DIR/logs" ]; then
    LATEST_LOG=$(ls -t "$WORK_DIR/logs"/service_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "最新日志: $LATEST_LOG"
        echo "日志大小: $(du -h "$LATEST_LOG" | cut -f1)"
        echo "最后修改: $(stat -c %y "$LATEST_LOG")"
    else
        echo "未找到日志文件"
    fi
else
    echo "日志目录不存在"
fi

echo ""
echo "=== 常用命令 ==="
echo "查看实时日志: tail -f $WORK_DIR/logs/service_*.log"
echo "停止服务: ./shell/stop_service.sh"
echo "重启服务: ./shell/restart_service.sh" 