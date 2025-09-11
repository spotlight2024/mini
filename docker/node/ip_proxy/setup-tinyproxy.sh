#!/bin/bash

# tinyproxy设置脚本 - 生成配置文件

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

# 生成tinyproxy配置
generate_tinyproxy_config() {
    local template="/opt/tinyproxy-setup/tinyproxy.conf.template"
    local config="/etc/tinyproxy/tinyproxy.conf"
    
    log "生成tinyproxy配置: $config"
    
    # 创建配置目录
    mkdir -p /etc/tinyproxy
    
    # 复制模板
    cp "$template" "$config"
    
    # 根据环境变量生成上游代理配置
    if [ -n "$PROXY_HOST" ] && [ -n "$PROXY_PORT" ]; then
        log "配置上游代理: $PROXY_HOST:$PROXY_PORT"
        
        # 构建上游代理配置
        if [ -n "$PROXY_USERNAME" ] && [ -n "$PROXY_PASSWORD" ]; then
            # tinyproxy的认证代理配置格式: upstream http user:pass@host:port
            local upstream_config="upstream http $PROXY_USERNAME:$PROXY_PASSWORD@$PROXY_HOST:$PROXY_PORT"
            log "使用认证代理: $PROXY_USERNAME@$PROXY_HOST:$PROXY_PORT"
        else
            # 无认证的代理
            local upstream_config="upstream http $PROXY_HOST:$PROXY_PORT"
            log "使用无认证代理: $PROXY_HOST:$PROXY_PORT"
        fi
        
        # 替换占位符
        sed -i "s|# UPSTREAM_PROXY_PLACEHOLDER|$upstream_config|g" "$config"
    else
        warn "未配置上游代理，将使用直连"
        sed -i "s|# UPSTREAM_PROXY_PLACEHOLDER||g" "$config" # 移除占位符
    fi
    
    # 设置正确的权限
    chown nobody:nogroup "$config"
    chmod 644 "$config"
    
    log "✅ tinyproxy配置生成完成"
}

# 验证配置
validate_config() {
    if [ -n "$PROXY_HOST" ] && [ -n "$PROXY_PORT" ]; then
        log "✅ 检测到代理配置:"
        log "   主机: $PROXY_HOST"
        log "   端口: $PROXY_PORT"
        log "   用户: ${PROXY_USERNAME:-未设置}"
        
        if [ -n "$PROXY_USERNAME" ] && [ -n "$PROXY_PASSWORD" ]; then
            log "   认证: 已配置"
        else
            warn "   认证: 未配置（将使用无认证模式）"
        fi
    else
        warn "⚠️  未检测到代理配置，将使用直连模式"
    fi
}

# 主函数
main() {
    log "🔧 tinyproxy透明代理设置"
    
    validate_config
    generate_tinyproxy_config
    
    log "🎉 tinyproxy设置完成"
}

# 运行主函数
main "$@"
