#!/bin/bash

# 代理切换脚本 - 由Java代码调用，更新tinyproxy配置
# 参数: proxy_ip proxy_port proxy_username proxy_password

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SWITCH:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# 检查参数
if [ $# -lt 4 ]; then
    error "参数不足，需要: proxy_ip proxy_port proxy_username proxy_password"
    exit 1
fi

PROXY_IP="$1"
PROXY_PORT="$2"
PROXY_USERNAME="$3"
PROXY_PASSWORD="$4"

# 配置路径
CONFIG_PATH="/shared/config/tinyproxy.conf"
SIGNAL_PATH="/shared/config/reload.signal"
LOCK_PATH="/shared/config/proxy.lock"

log "开始切换代理配置: ${PROXY_USERNAME:+$PROXY_USERNAME@}$PROXY_IP:$PROXY_PORT"

# 获取文件锁
acquire_lock() {
    local timeout=5
    local count=0
    
    while [ $count -lt $((timeout * 10)) ]; do
        if (set -C; echo $$ > "$LOCK_PATH") 2>/dev/null; then
            log "获取配置锁成功"
            return 0
        fi
        sleep 0.1
        count=$((count + 1))
    done
    
    error "获取配置锁超时"
    return 1
}

# 释放文件锁
release_lock() {
    rm -f "$LOCK_PATH"
    log "配置锁已释放"
}

# 生成tinyproxy配置
generate_config() {
    local config_file="$1"
    local proxy_ip="$2"
    local proxy_port="$3"
    local proxy_user="$4"
    local proxy_pass="$5"
    
    log "生成新的tinyproxy配置文件"
    
    # 检查代理配置模式
    if [ -n "$proxy_ip" ] && [ -n "$proxy_port" ]; then
        if [ -n "$proxy_user" ] && [ -n "$proxy_pass" ]; then
            log "配置模式: 认证代理 - $proxy_user@$proxy_ip:$proxy_port"
        else
            log "配置模式: 无认证代理 - $proxy_ip:$proxy_port"
        fi
    else
        log "配置模式: 直连访问 - 使用服务器本身IP"
    fi
    
    cat > "$config_file" << EOF
# tinyproxy配置 - 动态生成 by Java Switch Script
# Generated at: $(date)

# 基础配置
User nobody
Group nogroup
Port 3128

# 日志配置 - 输出到stdout便于kubectl logs查看
LogFile "/dev/stdout"
LogLevel Info

EOF

    # 根据参数决定是否配置上游代理
    if [ -n "$proxy_ip" ] && [ -n "$proxy_port" ]; then
        echo "# 上游代理配置" >> "$config_file"
        if [ -n "$proxy_user" ] && [ -n "$proxy_pass" ]; then
            # 认证代理 - 为所有流量设置默认上游代理
            echo "upstream http $proxy_user:$proxy_pass@$proxy_ip:$proxy_port" >> "$config_file"
            log "已配置认证代理: $proxy_user@$proxy_ip:$proxy_port"
        else
            # 无认证代理 - 为所有流量设置默认上游代理
            echo "upstream http $proxy_ip:$proxy_port" >> "$config_file"
            log "已配置无认证代理: $proxy_ip:$proxy_port"
        fi
        echo "" >> "$config_file"
    else
        echo "# 直连模式 - 无上游代理配置" >> "$config_file"
        echo "" >> "$config_file"
        log "已配置直连模式"
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

    log "配置文件生成完成"
}

# 发送重载信号
send_reload_signal() {
    echo "$(date +%s)" > "$SIGNAL_PATH"
    log "重载信号已发送"
}

# 等待重载完成
wait_for_reload() {
    local timeout=5
    local count=0
    
    log "等待sidecar重载完成..."
    
    while [ $count -lt $((timeout * 10)) ]; do
        if [ ! -f "$SIGNAL_PATH" ]; then
            log "重载完成"
            return 0
        fi
        sleep 0.1
        count=$((count + 1))
    done
    
    warn "等待重载超时"
    return 1
}

# 主流程
main() {
    # 1. 获取锁
    if ! acquire_lock; then
        exit 1
    fi
    
    # 确保释放锁
    trap 'release_lock; exit 1' INT TERM EXIT
    
    # 2. 生成配置
    generate_config "$CONFIG_PATH" "$PROXY_IP" "$PROXY_PORT" "$PROXY_USERNAME" "$PROXY_PASSWORD"
    
    # 3. 发送重载信号
    send_reload_signal
    
    # 4. 等待重载完成
    if wait_for_reload; then
        log "代理切换成功: ${PROXY_USERNAME:+$PROXY_USERNAME@}$PROXY_IP:$PROXY_PORT"
        # 正常退出，trap会释放锁
        trap - INT TERM EXIT
        release_lock
        exit 0
    else
        error "代理切换失败: 重载超时"
        # trap会释放锁
        exit 1
    fi
}

# 运行主函数
main "$@"

