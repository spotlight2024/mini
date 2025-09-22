#!/bin/bash

# tinyproxy Sidecar 启动脚本
# 用于Kubernetes Pod中的代理sidecar容器

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# 生成tinyproxy配置文件
generate_config() {
    local config_file="/shared/config/tinyproxy.conf"
    local proxy_host="${1}"
    local proxy_port="${2}"
    local proxy_user="${3}"
    local proxy_pass="${4}"
    
    log "生成tinyproxy配置文件: $config_file"
    
    # 检查代理配置模式
    if [ -n "$proxy_host" ] && [ -n "$proxy_port" ]; then
        if [ -n "$proxy_user" ] && [ -n "$proxy_pass" ]; then
            info "模式: 认证代理 - $proxy_user@$proxy_host:$proxy_port"
        else
            info "模式: 无认证代理 - $proxy_host:$proxy_port"
        fi
    else
        info "模式: 直连访问 - 使用服务器本身IP"
    fi
    
    cat > "$config_file" << EOF
# tinyproxy配置 - 动态生成 by Sidecar
# Generated at: $(date)

# 基础配置
User root
Group root
Port 3128

# 日志配置 - 输出到stdout便于kubectl logs查看
LogFile "/dev/stdout"
LogLevel Info

EOF

    # 只有当代理配置存在时才添加upstream
    if [ -n "$proxy_host" ] && [ -n "$proxy_port" ]; then
        echo "# 上游代理配置" >> "$config_file"
        if [ -n "$proxy_user" ] && [ -n "$proxy_pass" ]; then
            # 认证代理 - 为所有流量设置默认上游代理
            echo "upstream http $proxy_user:$proxy_pass@$proxy_host:$proxy_port" >> "$config_file"
            info "使用认证代理: $proxy_user@$proxy_host:$proxy_port"
        else
            # 无认证代理 - 为所有流量设置默认上游代理
            echo "upstream http $proxy_host:$proxy_port" >> "$config_file"
            info "使用无认证代理: $proxy_host:$proxy_port"
        fi
        echo "" >> "$config_file"
    else
        echo "# 无上游代理 - 直接访问模式" >> "$config_file"
        echo "" >> "$config_file"
    fi

    cat >> "$config_file" << EOF

# 访问控制
Allow 127.0.0.1
Allow 0.0.0.0/0

# 性能优化
MaxClients 100
MinSpareServers 5
MaxSpareServers 20
StartServers 10
MaxRequestsPerChild 0

# 连接超时和端口
Timeout 600
ConnectPort 443
ConnectPort 563
ConnectPort 80
ConnectPort 8080
ConnectPort 3128

# End of configuration
EOF

    log "✅ tinyproxy配置文件生成完成"
}

# 启动tinyproxy进程
start_tinyproxy() {
    log "启动tinyproxy进程..."
    
    # 启动tinyproxy (使用-d保持前台运行，便于进程管理)
    tinyproxy -d -c /shared/config/tinyproxy.conf &
    PROXY_PID=$!
    
    # 等待启动
    sleep 2
    
    # 验证进程
    if kill -0 $PROXY_PID 2>/dev/null; then
        log "✅ tinyproxy已启动，PID: $PROXY_PID，监听端口: 3128"
        return 0
    else
        error "❌ tinyproxy启动失败"
        return 1
    fi
}

# 重载tinyproxy配置
reload_tinyproxy() {
    log "重载tinyproxy配置..."
    
    # 先尝试热重载
    if kill -HUP $PROXY_PID 2>/dev/null; then
        log "✅ tinyproxy热重载成功"
        return 0
    else
        warn "HUP信号失败，重启进程..."
        
        # 强制重启
        kill $PROXY_PID 2>/dev/null || true
        sleep 1
        
        if start_tinyproxy; then
            log "🔄 tinyproxy重启完成，新PID: $PROXY_PID"
            return 0
        else
            error "❌ tinyproxy重启失败"
            return 1
        fi
    fi
}

# 信号文件监控循环
monitor_signals() {
    log "📡 开始监控重载信号..."
    
    while true; do
        # 检查重载信号
        if [ -f "/shared/config/reload.signal" ]; then
            info "⚡ 检测到重载信号，执行重载..."
            
            if reload_tinyproxy; then
                log "🎉 重载完成"
            else
                error "❌ 重载失败"
            fi
            
            # 清除信号文件
            rm -f /shared/config/reload.signal
            log "🧹 信号文件已清除"
        fi
        
        # 检查进程健康状态
        if ! kill -0 $PROXY_PID 2>/dev/null; then
            warn "❌ tinyproxy进程意外终止，重启..."
            
            if start_tinyproxy; then
                log "🔄 tinyproxy健康检查重启完成，新PID: $PROXY_PID"
            else
                error "❌ 健康检查重启失败，等待下次检查..."
                sleep 5
                continue
            fi
        fi
        
        # 500ms检查一次，保证快速响应
        sleep 0.5
    done
}

# 显示架构信息
show_architecture() {
    echo ""
    echo "🏗️  Kubernetes Sidecar代理架构:"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│                   Pod                                    │"
    echo "│  ┌─────────────┐        ┌──────────────────────┐       │"
    echo "│  │ chrome-node │        │  proxy-sidecar       │───────┼──▶ 上游代理"
    echo "│  │ (selenium)  │        │  tinyproxy:3128      │       │    动态切换IP"
    echo "│  │ HTTP_PROXY  │◀──────│  热重载支持           │       │"
    echo "│  │ 127.0.0.1:3128      │  日志输出stdout      │       │"
    echo "│  └─────────────┘        └──────────────────────┘       │"
    echo "│           ↕                        ↕                   │"
    echo "│    /shared/config (emptyDir Volume)                    │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo ""
}

# 主函数
main() {
    log "🚀 tinyproxy Sidecar启动中..."
    
    show_architecture
    
    # 创建共享配置目录
    mkdir -p /shared/config
    log "📁 共享配置目录已创建: /shared/config"
    
    # 生成初始配置 (不设置上游代理，等待Java代码动态配置)
    generate_config "" "" "" ""
    
    # 启动tinyproxy
    if ! start_tinyproxy; then
        error "❌ 初始启动失败，退出"
        exit 1
    fi
    
    # 开始监控信号
    monitor_signals
}

# 信号处理
trap 'log "📡 收到终止信号，清理进程..."; kill $PROXY_PID 2>/dev/null || true; exit 0' TERM INT

# 运行主函数
main "$@"
