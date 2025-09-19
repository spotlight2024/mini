#!/bin/bash

# 自定义入口脚本 - 业务逻辑处理，代理由sidecar提供

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
    echo "🏗️  Kubernetes Sidecar代理架构:"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│                   Pod                                    │"
    echo "│  ┌─────────────┐        ┌──────────────────────┐       │"
    echo "│  │ chrome-node │        │  proxy-sidecar       │───────┼──▶ 上游代理"
    echo "│  │ (业务逻辑)   │        │  tinyproxy:3128      │       │    动态切换IP"
    echo "│  │ HTTP_PROXY  │◀──────│  热重载支持           │       │"
    echo "│  │ 127.0.0.1:3128      │  日志输出stdout      │       │"
    echo "│  └─────────────┘        └──────────────────────┘       │"
    echo "│           ↕                        ↕                   │"
    echo "│    /shared/config (emptyDir Volume)                    │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo ""
}

# 检查sidecar代理状态 (非阻塞)
check_sidecar_status() {
    log "🔍 检查sidecar代理状态..."
    
    if curl -s --max-time 3 --proxy http://127.0.0.1:3128 http://httpbin.org/ip > /dev/null 2>&1; then
        log "✅ sidecar代理服务已就绪"
        return 0
    else
        warn "⚠️  sidecar代理服务暂未就绪，Chrome将在代理可用时自动连接"
        return 1
    fi
}

# 设置代理环境变量
setup_proxy_env() {
    log "🔧 设置sidecar代理环境变量..."
    
    # 设置HTTP代理环境变量，指向sidecar的tinyproxy
    export HTTP_PROXY="http://127.0.0.1:3128"
    export HTTPS_PROXY="http://127.0.0.1:3128"
    export http_proxy="http://127.0.0.1:3128"
    export https_proxy="http://127.0.0.1:3128"
    
    log "📝 代理环境变量已设置: HTTP_PROXY=$HTTP_PROXY"
}

# 主函数
main() {
    log "🚀 启动Chrome节点 (Sidecar代理架构)"
    
    # 显示架构信息
    show_architecture
    
    # 复制sidecar脚本到共享目录供sidecar容器使用
    log "📋 复制脚本到共享目录..."
    mkdir -p /shared/scripts
    cp /opt/node-setup/tinyproxy-sidecar.sh /shared/scripts/
    cp /opt/node-setup/switch-proxy.sh /shared/scripts/
    chmod +x /shared/scripts/*.sh
    log "✅ 脚本已复制到 /shared/scripts/ (tinyproxy-sidecar.sh, switch-proxy.sh)"
    
    # 显示节点信息
    echo "📋 节点配置:"
    echo "   容器名: $HOSTNAME"
    echo "   Hub地址: ${SE_EVENT_BUS_HOST:-selenium-hub}"
    echo "   代理方式: Sidecar (127.0.0.1:3128)"
    echo "   脚本共享: /shared/scripts/"
    echo ""
    
    # 检查sidecar代理状态 (非阻塞)
    # check_sidecar_status
    
    # 设置代理环境变量
    setup_proxy_env
    
    log "🎯 启动原始selenium节点..."
    
    # 确保环境变量传递给selenium进程
    export HTTP_PROXY="http://127.0.0.1:3128"
    export HTTPS_PROXY="http://127.0.0.1:3128"
    export http_proxy="http://127.0.0.1:3128"
    export https_proxy="http://127.0.0.1:3128"
    
    # 设置Chrome稳定性参数 (保留您的业务逻辑)
    export SE_CHROME_ARGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --disable-features=VizDisplayCompositor --disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows --disable-ipc-flooding-protection --memory-pressure-off"
    
    log "📝 最终确认环境变量: HTTP_PROXY=$HTTP_PROXY"
    log "🔧 Chrome稳定性参数已设置"
    
    # 调用原始的selenium入口点，传递所有参数和环境变量
    exec /opt/bin/entry_point.sh "$@"
}

# 运行主函数
main "$@"
