#!/bin/bash

# ADB 代理服务停止脚本

set -e

echo "=== 停止 ADB 代理服务 ==="

# 停止 ADB 服务
echo "停止 ADB 服务..."
adb kill-server 2>/dev/null || true
echo "ADB 服务已停止"

# 检查PID文件是否存在
if [ -f /opt/scripts/adb_proxy.pid ]; then
    PID=$(cat /opt/scripts/adb_proxy.pid)
    echo "找到 ADB 代理服务 PID: $PID"
    
    # 检查进程是否还在运行
    if ps -p $PID > /dev/null; then
        echo "正在停止 ADB 代理服务 (PID: $PID)..."
        kill $PID
        
        # 等待进程结束
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null; then
                echo "✓ ADB 代理服务已停止"
                rm -f /opt/scripts/adb_proxy.pid
                break
            fi
            sleep 1
        done
        
        # 如果进程还在运行，强制杀死
        if ps -p $PID > /dev/null; then
            echo "强制停止 ADB 代理服务..."
            kill -9 $PID
            rm -f /opt/scripts/adb_proxy.pid
        fi
    else
        echo "ADB 代理服务进程已不存在"
        rm -f /opt/scripts/adb_proxy.pid
    fi
else
    echo "未找到 ADB 代理服务 PID 文件"
fi

echo "=== ADB 代理服务停止完成 ===" 