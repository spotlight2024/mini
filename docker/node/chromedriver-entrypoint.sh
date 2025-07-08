#!/bin/bash

# ChromeDriver Node 启动脚本
# 基于 appium-docker-android 项目的启动逻辑

set -e

# 设置默认值
export NODE_CONFIG_PATH=${NODE_CONFIG_PATH:-"/opt/selenium/chromedriver-node.toml"}
export SELENIUM_HUB_HOST=${SELENIUM_HUB_HOST:-"selenium-hub"}
export SELENIUM_HUB_PORT=${SELENIUM_HUB_PORT:-"4444"}
export NODE_PORT=${NODE_PORT:-"5555"}
export MAX_SESSIONS=${MAX_SESSIONS:-"3"}

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ChromeDriver-Node: $1"
}

log "ChromeDriver Node 启动中..."

# 检查 ChromeDriver 是否可用
if [ ! -x "/opt/chromedriver/chromedriver" ]; then
    log "错误: ChromeDriver 不存在或不可执行"
    exit 1
fi

# 验证 ChromeDriver 版本
CHROMEDRIVER_VER=$(/opt/chromedriver/chromedriver --version 2>/dev/null || echo "unknown")
log "ChromeDriver 版本: $CHROMEDRIVER_VER"

# 注意：此节点仅包含 ChromeDriver，不包含 Chrome 浏览器
log "注意: 此节点专用于 Android WebView 和远程 Chrome 实例的自动化测试"

# # 启动 Xvfb (虚拟显示服务器)
# if [ "$HEADLESS" != "false" ]; then
#     log "启动 Xvfb 虚拟显示服务器..."
#     Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
#     export DISPLAY=:99
# fi

# ADB 相关配置
if [ "$ENABLE_ADB" = "true" ] || [ "$REMOTE_ADB" = "true" ]; then
    log "配置 ADB 连接..."
    
    # 创建 ADB 配置目录
    mkdir -p ~/.android
    
    if [ "$REMOTE_ADB" = "true" ] && [ -n "$ANDROID_DEVICES" ]; then
        log "连接远程 Android 设备: $ANDROID_DEVICES"
        
        # 启动 ADB 服务器
        adb start-server
        
        # 连接到指定的设备
        IFS=',' read -ra DEVICES <<< "$ANDROID_DEVICES"
        for device in "${DEVICES[@]}"; do
            log "尝试连接设备: $device"
            adb connect "$device" || log "连接设备 $device 失败"
        done
        
        # 列出已连接的设备
        log "已连接的设备列表:"
        adb devices
        
        # 后台监控设备连接状态
        {
            while true; do
                sleep ${REMOTE_ADB_POLLING_SEC:-60}
                for device in "${DEVICES[@]}"; do
                    if ! adb devices | grep -q "$device"; then
                        log "重新连接设备: $device"
                        adb connect "$device" || log "重连设备 $device 失败"
                    fi
                done
            done
        } &
    fi
    
    # 检查设备连接状态
    DEVICE_COUNT=$(adb devices | grep -c "device$" || echo "0")
    log "检测到 $DEVICE_COUNT 个已连接的 Android 设备"
fi

# 等待 Selenium Hub 就绪
log "等待 Selenium Hub ($SELENIUM_HUB_HOST:$SELENIUM_HUB_PORT) 就绪..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -sSf "http://$SELENIUM_HUB_HOST:$SELENIUM_HUB_PORT/status" >/dev/null 2>&1; then
        log "Selenium Hub 已就绪"
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    log "警告: 等待 Selenium Hub 超时，但继续启动节点"
fi

# 检查配置文件
if [ ! -f "$NODE_CONFIG_PATH" ]; then
    log "错误: 节点配置文件不存在: $NODE_CONFIG_PATH"
    exit 1
fi

log "使用配置文件: $NODE_CONFIG_PATH"

# 设置环境变量
export SE_EVENT_BUS_HOST="$SELENIUM_HUB_HOST"
export SE_EVENT_BUS_PUBLISH_PORT=4442
export SE_EVENT_BUS_SUBSCRIBE_PORT=4443

# 启动 Selenium Node
log "启动 ChromeDriver Selenium Node..."
log "节点端口: $NODE_PORT"
log "最大会话数: $MAX_SESSIONS"

# 直接启动 Selenium Grid Node，使用我们的自定义配置
exec java -jar /opt/selenium/selenium-server.jar node --config "$NODE_CONFIG_PATH" 