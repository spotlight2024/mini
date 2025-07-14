#!/bin/bash

# ADB 初始化脚本
# 此脚本用于在容器启动时初始化 ADB 服务

set -e

echo "=== ADB 初始化脚本开始执行 ==="
echo "执行时间: $(date)"

# 检查 ADB 是否安装
if ! command -v adb &> /dev/null; then
    echo "错误: ADB 未安装"
    exit 1
fi

echo "✓ ADB 已安装: $(adb version | head -n1)"

# 启动 ADB 服务器
echo "启动 ADB 服务器..."
adb start-server

# 等待 ADB 服务器启动
sleep 2

# 检查 ADB 服务器状态
if adb devices &> /dev/null; then
    echo "✓ ADB 服务器启动成功"
else
    echo "✗ ADB 服务器启动失败"
    exit 1
fi

# 显示连接的设备
echo "当前连接的设备:"
adb devices

# 设置 ADB 配置
echo "配置 ADB 设置..."

# 设置 ADB 超时时间
adb shell settings put global adb_wifi_enabled 1 2>/dev/null || echo "无法设置 ADB WiFi 模式"

# 创建 ADB 日志目录
mkdir -p /opt/scripts/logs/adb

# 记录 ADB 初始化日志
cat > /opt/scripts/logs/adb/init.log << EOF
ADB 初始化时间: $(date)
ADB 版本: $(adb version | head -n1)
ADB 服务器状态: 运行中
连接设备数量: $(adb devices | grep -v "List of devices" | grep -v "^$" | wc -l)
EOF

echo "✓ ADB 初始化完成"
echo "ADB 日志位置: /opt/scripts/logs/adb/init.log"

# 如果传入了设备连接参数，尝试连接设备
if [ ! -z "$ADB_DEVICE_IP" ]; then
    echo "尝试连接到设备: $ADB_DEVICE_IP"
    adb connect "$ADB_DEVICE_IP" 2>/dev/null || echo "无法连接到设备 $ADB_DEVICE_IP"
fi

echo "=== ADB 初始化脚本执行完成 ===" 

adb connect "123.56.152.41:6529"

adb devices