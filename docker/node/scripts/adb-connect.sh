#!/bin/bash

# ADB动态设备连接脚本
# 根据TARGET_SERIAL_ID环境变量连接指定的Android设备

set -e

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ADB-Connect: $1"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ADB-Connect ERROR: $1" >&2
}

# 检查必需的环境变量
if [ -z "$TARGET_SERIAL_ID" ]; then
    error "TARGET_SERIAL_ID 环境变量未设置"
    exit 1
fi

log "开始连接Android设备: $TARGET_SERIAL_ID"

# 设置ADB超时时间
ADB_TIMEOUT=${ADB_TIMEOUT:-30}

# 启动ADB服务器
log "启动ADB服务器..."
adb start-server

# 连接到设备
log "尝试连接设备: $TARGET_SERIAL_ID"
if adb connect "$TARGET_SERIAL_ID"; then
    log "设备连接成功: $TARGET_SERIAL_ID"
else
    error "设备连接失败: $TARGET_SERIAL_ID"
    exit 1
fi

# 等待设备就绪
log "等待设备就绪..."
timeout_count=0
while [ $timeout_count -lt $ADB_TIMEOUT ]; do
    if adb -s "$TARGET_SERIAL_ID" shell echo "ready" >/dev/null 2>&1; then
        log "设备就绪: $TARGET_SERIAL_ID"
        break
    fi
    
    sleep 1
    timeout_count=$((timeout_count + 1))
    
    if [ $timeout_count -eq $ADB_TIMEOUT ]; then
        error "设备就绪超时: $TARGET_SERIAL_ID"
        exit 1
    fi
done

# 验证设备连接状态
log "验证设备连接状态..."
if adb devices | grep -q "$TARGET_SERIAL_ID.*device"; then
    log "设备验证成功: $TARGET_SERIAL_ID"
    
    # 显示设备信息
    DEVICE_MODEL=$(adb -s "$TARGET_SERIAL_ID" shell getprop ro.product.model 2>/dev/null || echo "Unknown")
    ANDROID_VERSION=$(adb -s "$TARGET_SERIAL_ID" shell getprop ro.build.version.release 2>/dev/null || echo "Unknown")
    
    log "设备型号: $DEVICE_MODEL"
    log "Android版本: $ANDROID_VERSION"
    
    # 输出连接的设备列表
    log "当前已连接的设备:"
    adb devices
    
else
    error "设备验证失败: $TARGET_SERIAL_ID"
    log "当前设备列表:"
    adb devices
    exit 1
fi

# 可选：设置Chrome调试端口转发
if [ "$ENABLE_CHROME_DEBUG" = "true" ]; then
    CHROME_DEBUG_PORT=${CHROME_DEBUG_PORT:-9222}
    log "设置Chrome调试端口转发: $CHROME_DEBUG_PORT"
    adb -s "$TARGET_SERIAL_ID" forward tcp:$CHROME_DEBUG_PORT localabstract:chrome_devtools_remote
fi

log "ADB设备连接完成: $TARGET_SERIAL_ID" 