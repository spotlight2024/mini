#!/bin/bash

# 自定义入口脚本 - 启动tinyproxy然后调用原始selenium入口点

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"
}

# 显示架构信息
show_architecture() {
    echo ""
    echo "🏗️  tinyproxy透明代理架构 (Chrome完全无感知):"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│                   Chrome Node                            │"
    echo "│  ┌─────────────┐        ┌──────────────────────┐       │"
    echo "│  │   Chrome    │        │  tinyproxy (8888)    │───────┼──▶ 上游代理"
    echo "│  │  (完全无感知) │        │  (轻量级实现)         │       │    ${PROXY_HOST:-未配置}:${PROXY_PORT:-N/A}"
    echo "│  │  (无弹窗)    │        │  (支持认证)           │       │    ${PROXY_USERNAME:-未配置}:****"
    echo "│  │  (HTTP_PROXY)│◀──────│                      │       │"
    echo "│  └─────────────┘        └──────────────────────┘       │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo ""
}

# 启动tinyproxy作为后台进程
start_tinyproxy() {
    log "🚀 启动tinyproxy透明代理..."
    
    show_architecture
    
    # 以root身份设置tinyproxy，确保环境变量正确传递
    log "🔧 传递代理配置: $PROXY_HOST:$PROXY_PORT (用户: $PROXY_USERNAME)"
    sudo env PROXY_HOST="$PROXY_HOST" PROXY_PORT="$PROXY_PORT" PROXY_USERNAME="$PROXY_USERNAME" PROXY_PASSWORD="$PROXY_PASSWORD" /opt/tinyproxy-setup/setup-tinyproxy.sh
    
    # 以nobody身份启动tinyproxy
    sudo /usr/bin/tinyproxy -d -c /etc/tinyproxy/tinyproxy.conf &
    
    # 等待tinyproxy启动
    sleep 3
    
    # 验证tinyproxy是否启动
    if curl -s --max-time 5 --proxy http://127.0.0.1:8888 http://httpbin.org/ip > /dev/null 2>&1; then
        log "✅ tinyproxy启动成功并可正常工作"
    else
        warn "⚠️  tinyproxy可能未正常启动，但继续启动selenium"
    fi
}

# 设置代理环境变量
setup_proxy_env() {
    log "🔧 设置透明代理环境变量..."
    
    # 设置HTTP代理环境变量，让Chrome透明使用代理
    export HTTP_PROXY="http://127.0.0.1:8888"
    export HTTPS_PROXY="http://127.0.0.1:8888"
    export http_proxy="http://127.0.0.1:8888"
    export https_proxy="http://127.0.0.1:8888"
    
    log "📝 代理环境变量已设置: HTTP_PROXY=$HTTP_PROXY"
}

# 主函数
main() {
    log "🚀 启动Chrome节点 (tinyproxy透明代理架构)"
    
    # 显示节点信息
    echo "📋 节点配置:"
    echo "   容器名: $HOSTNAME"
    echo "   Hub地址: ${SE_EVENT_BUS_HOST:-selenium-hub}"
    echo "   上游代理: ${PROXY_HOST:-未配置}:${PROXY_PORT:-N/A}"
    echo "   代理用户: ${PROXY_USERNAME:-未配置}"
    echo ""
    
    # 启动tinyproxy
    start_tinyproxy
    
    # 设置代理环境变量
    setup_proxy_env
    
    log "🎯 启动原始selenium节点..."
    
    # 确保环境变量传递给selenium进程
    export HTTP_PROXY="http://127.0.0.1:8888"
    export HTTPS_PROXY="http://127.0.0.1:8888"
    export http_proxy="http://127.0.0.1:8888"
    export https_proxy="http://127.0.0.1:8888"
    
    # 设置Chrome稳定性参数
    export SE_CHROME_ARGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --disable-features=VizDisplayCompositor --disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows --disable-ipc-flooding-protection --memory-pressure-off"
    
    log "📝 最终确认环境变量: HTTP_PROXY=$HTTP_PROXY"
    log "🔧 Chrome稳定性参数已设置"
    
    # 调用原始的selenium入口点，传递所有参数和环境变量
    exec /opt/bin/entry_point.sh "$@"
}

# 运行主函数
main "$@"
