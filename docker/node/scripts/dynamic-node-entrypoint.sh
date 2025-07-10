#!/bin/bash

# Chrome 128 动态Node入口脚本
# 支持基于serial_id的动态设备连接和Selenium Node启动

set -e

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dynamic-Node: $1"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dynamic-Node ERROR: $1" >&2
}

log "Chrome 128 动态Node启动中..."

# 检查必需环境变量
if [ -z "$TARGET_SERIAL_ID" ]; then
    error "TARGET_SERIAL_ID 环境变量未设置"
    exit 1
fi

# 设置默认值
export SELENIUM_HUB_HOST=${SELENIUM_HUB_HOST:-"selenium-hub"}
export SELENIUM_HUB_PORT=${SELENIUM_HUB_PORT:-"4444"}
export NODE_PORT=${NODE_PORT:-"5555"}
export MAX_SESSIONS=${MAX_SESSIONS:-"1"}

log "配置信息:"
log "  目标设备: $TARGET_SERIAL_ID"
log "  Selenium Hub: $SELENIUM_HUB_HOST:$SELENIUM_HUB_PORT"
log "  节点端口: $NODE_PORT"
log "  最大会话数: $MAX_SESSIONS"

# 第一步：连接ADB设备
log "步骤1: 连接Android设备..."
if ! /opt/bin/adb-connect.sh; then
    error "ADB设备连接失败"
    exit 1
fi
log "ADB设备连接成功"

# 第二步：等待Selenium Hub就绪
log "步骤2: 等待Selenium Hub就绪..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -sSf "http://$SELENIUM_HUB_HOST:$SELENIUM_HUB_PORT/status" >/dev/null 2>&1; then
        log "Selenium Hub已就绪"
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    error "等待Selenium Hub超时"
    exit 1
fi

# 第三步：生成动态节点配置
log "步骤3: 生成动态节点配置..."
NODE_CONFIG="/tmp/node-config-$TARGET_SERIAL_ID.toml"

# 生成唯一节点ID
NODE_ID="chrome-128-$(echo $TARGET_SERIAL_ID | tr ':.' '-')-$(date +%s)"

cat > "$NODE_CONFIG" << EOF
[server]
port = $NODE_PORT

[node]
detect-drivers = false
max-sessions = $MAX_SESSIONS
session-timeout = "300s"

[events]
publish = "tcp://$SELENIUM_HUB_HOST:4442"
subscribe = "tcp://$SELENIUM_HUB_HOST:4443"

[[node.driver-configuration]]
display-name = "Chrome 128 Android WebView - $TARGET_SERIAL_ID"
stereotype = '{"browserName": "chrome", "browserVersion": "128", "platformName": "android", "se:serial_id": "$TARGET_SERIAL_ID", "se:node_id": "$NODE_ID"}'
webdriver-executable = "/usr/bin/chromedriver"
max-sessions = $MAX_SESSIONS

[logging]
level = "INFO"
plain-logs = false
EOF

log "节点配置已生成: $NODE_CONFIG"
log "节点ID: $NODE_ID"

# 第四步：设置Selenium Grid事件总线环境变量
export SE_EVENT_BUS_HOST="$SELENIUM_HUB_HOST"
export SE_EVENT_BUS_PUBLISH_PORT=4442
export SE_EVENT_BUS_SUBSCRIBE_PORT=4443

# 第五步：启动Chrome浏览器进程管理（如果需要）
log "步骤4: 配置Chrome进程环境..."

# 设置Chrome远程调试选项
export CHROME_OPTIONS="--remote-debugging-address=0.0.0.0 --remote-debugging-port=9222 --disable-gpu --no-sandbox --disable-dev-shm-usage"

# 第六步：启动Selenium Node
log "步骤5: 启动Selenium Node..."
log "使用配置文件: $NODE_CONFIG"

# 注册清理函数
cleanup() {
    log "正在清理资源..."
    if [ -n "$TARGET_SERIAL_ID" ]; then
        log "断开ADB设备连接: $TARGET_SERIAL_ID"
        adb disconnect "$TARGET_SERIAL_ID" || true
    fi
    log "清理完成"
}
trap cleanup EXIT

# 启动Selenium Grid Node
exec java \
    -Dwebdriver.chrome.driver=/usr/bin/chromedriver \
    -Dwebdriver.chrome.args="$CHROME_OPTIONS" \
    -jar /opt/selenium/selenium-server.jar \
    node \
    --config "$NODE_CONFIG" \
    --detect-drivers false 