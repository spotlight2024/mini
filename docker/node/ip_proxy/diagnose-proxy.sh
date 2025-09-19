#!/bin/bash

# tinyproxy代理诊断脚本
# 用于排查K8S环境中的代理连接问题

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

# 1. 检查环境变量
check_environment() {
    echo "================================"
    info "🔍 1. 检查环境变量配置"
    echo "================================"
    
    echo "代理配置环境变量:"
    echo "  PROXY_HOST: ${PROXY_HOST:-❌ 未设置}"
    echo "  PROXY_PORT: ${PROXY_PORT:-❌ 未设置}"
    echo "  PROXY_USERNAME: ${PROXY_USERNAME:-❌ 未设置}"
    echo "  PROXY_PASSWORD: ${PROXY_PASSWORD:+✅ 已设置}${PROXY_PASSWORD:-❌ 未设置}"
    
    echo ""
    echo "本地代理环境变量:"
    echo "  HTTP_PROXY: ${HTTP_PROXY:-❌ 未设置}"
    echo "  HTTPS_PROXY: ${HTTPS_PROXY:-❌ 未设置}"
    
    if [ -z "$PROXY_HOST" ] || [ -z "$PROXY_PORT" ]; then
        error "❌ 关键环境变量缺失，这可能是配置问题的根源"
        return 1
    else
        log "✅ 基本环境变量已设置"
    fi
}

# 2. 检查tinyproxy配置文件
check_tinyproxy_config() {
    echo ""
    echo "================================"
    info "🔍 2. 检查tinyproxy配置文件"
    echo "================================"
    
    local config="/etc/tinyproxy/tinyproxy.conf"
    
    if [ ! -f "$config" ]; then
        error "❌ 配置文件不存在: $config"
        return 1
    fi
    
    echo "配置文件内容 ($config):"
    echo "----------------------------------------"
    cat "$config"
    echo "----------------------------------------"
    
    echo ""
    info "关键配置检查:"
    
    # 检查上游代理配置
    if grep -q "upstream http" "$config"; then
        local upstream_line=$(grep "upstream http" "$config")
        log "✅ 发现上游代理配置: $upstream_line"
        
        # 检查是否包含认证信息
        if echo "$upstream_line" | grep -q "@"; then
            log "✅ 配置包含认证信息"
        else
            warn "⚠️  配置不包含认证信息（可能是无认证代理）"
        fi
    else
        error "❌ 未找到上游代理配置！"
        return 1
    fi
    
    # 检查占位符是否被替换
    if grep -q "UPSTREAM_PROXY_PLACEHOLDER" "$config"; then
        error "❌ 占位符未被替换，脚本可能没有正确执行"
        return 1
    fi
}

# 3. 检查tinyproxy进程状态
check_tinyproxy_process() {
    echo ""
    echo "================================"
    info "🔍 3. 检查tinyproxy进程状态"
    echo "================================"
    
    if pgrep -f tinyproxy > /dev/null; then
        local pid=$(pgrep -f tinyproxy)
        log "✅ tinyproxy进程正在运行 (PID: $pid)"
        
        echo ""
        echo "进程详细信息:"
        ps aux | grep tinyproxy | grep -v grep
        
    else
        error "❌ tinyproxy进程未运行"
        return 1
    fi
    
    # 检查端口监听
    if netstat -tlnp 2>/dev/null | grep :8888 > /dev/null; then
        log "✅ tinyproxy正在监听8888端口"
    else
        error "❌ 端口8888未监听"
    fi
}

# 4. 测试上游代理连接
test_upstream_connectivity() {
    echo ""
    echo "================================"
    info "🔍 4. 测试上游代理连接"
    echo "================================"
    
    if [ -z "$PROXY_HOST" ] || [ -z "$PROXY_PORT" ]; then
        error "❌ 无法测试，代理配置缺失"
        return 1
    fi
    
    local proxy_url="${PROXY_HOST}:${PROXY_PORT}"
    
    echo "测试连接到: $proxy_url"
    
    # 测试TCP连接
    if timeout 10 bash -c "</dev/tcp/${PROXY_HOST}/${PROXY_PORT}" 2>/dev/null; then
        log "✅ TCP连接到上游代理成功"
    else
        error "❌ TCP连接到上游代理失败！这是502错误的根本原因"
        
        # 进一步网络诊断
        echo ""
        warn "进行网络诊断:"
        
        echo "1. 尝试ping主机:"
        if ping -c 3 -W 5 "$PROXY_HOST" > /dev/null 2>&1; then
            log "   ✅ 主机可达"
        else
            error "   ❌ 主机不可达"
        fi
        
        echo "2. 检查DNS解析:"
        if nslookup "$PROXY_HOST" > /dev/null 2>&1; then
            log "   ✅ DNS解析正常"
        else
            warn "   ⚠️  DNS解析可能有问题"
        fi
        
        echo "3. 路由跟踪 (前5跳):"
        timeout 10 traceroute -m 5 "$PROXY_HOST" 2>/dev/null || warn "   ⚠️  无法进行路由跟踪"
        
        return 1
    fi
    
    # 如果有认证信息，测试HTTP代理
    if [ -n "$PROXY_USERNAME" ] && [ -n "$PROXY_PASSWORD" ]; then
        echo ""
        echo "测试HTTP代理认证:"
        if timeout 10 curl -x "${PROXY_USERNAME}:${PROXY_PASSWORD}@${proxy_url}" \
           -s --max-time 5 http://httpbin.org/ip > /dev/null; then
            log "✅ 认证代理连接成功"
        else
            error "❌ 认证代理连接失败"
            return 1
        fi
    fi
}

# 5. 测试本地tinyproxy
test_local_tinyproxy() {
    echo ""
    echo "================================"
    info "🔍 5. 测试本地tinyproxy功能"
    echo "================================"
    
    echo "1. 测试tinyproxy端口连接:"
    if timeout 5 bash -c "</dev/tcp/127.0.0.1/8888" 2>/dev/null; then
        log "✅ tinyproxy端口可连接"
    else
        error "❌ tinyproxy端口不可连接"
        return 1
    fi
    
    echo ""
    echo "2. 测试通过tinyproxy的HTTP请求:"
    local test_result=$(timeout 10 curl -x 127.0.0.1:8888 -s --max-time 5 http://httpbin.org/ip 2>&1)
    
    if echo "$test_result" | grep -q "origin"; then
        log "✅ 通过tinyproxy的HTTP请求成功"
        echo "响应: $test_result"
    elif echo "$test_result" | grep -q "502"; then
        error "❌ 返回502错误，确认上游代理连接问题"
        echo "错误详情: $test_result"
    else
        warn "⚠️  请求失败，详情:"
        echo "$test_result"
    fi
}

# 6. 检查日志
check_logs() {
    echo ""
    echo "================================"
    info "🔍 6. 检查相关日志"
    echo "================================"
    
    echo "tinyproxy日志:"
    echo "----------------------------------------"
    if [ -f "/var/log/tinyproxy/tinyproxy.log" ]; then
        tail -20 /var/log/tinyproxy/tinyproxy.log
    else
        warn "⚠️  tinyproxy日志文件不存在"
    fi
    echo "----------------------------------------"
}

# 7. 提供修复建议
provide_fix_suggestions() {
    echo ""
    echo "================================"
    info "🔧 修复建议"
    echo "================================"
    
    echo "基于诊断结果，可能的解决方案:"
    echo ""
    
    if [ -z "$PROXY_HOST" ] || [ -z "$PROXY_PORT" ]; then
        echo "1. ❗ 环境变量问题:"
        echo "   - 检查K8S部署配置中的环境变量设置"
        echo "   - 确保 PROXY_HOST 和 PROXY_PORT 正确传递"
    fi
    
    echo "2. 🌐 网络连接问题:"
    echo "   - 检查上游代理服务器是否正常运行"
    echo "   - 验证K8S集群是否能访问外部IP ${PROXY_HOST:-未知}:${PROXY_PORT:-未知}"
    echo "   - 检查K8S网络策略是否阻止了出站连接"
    
    echo "3. 🔐 认证问题:"
    echo "   - 如果代理需要认证，请取消注释 PROXY_USERNAME 和 PROXY_PASSWORD"
    echo "   - 验证认证信息是否正确"
    
    echo "4. 🔄 容器重启:"
    echo "   - 手动重新执行设置脚本: sudo /opt/tinyproxy-setup/setup-tinyproxy.sh"
    echo "   - 重启tinyproxy: sudo pkill tinyproxy && sudo /usr/bin/tinyproxy -d -c /etc/tinyproxy/tinyproxy.conf &"
    
    echo ""
    echo "立即修复命令:"
    echo "kubectl delete pod -l app=chrome-node -n selenium-grid"
    echo "kubectl get pods -n selenium-grid -w"
}

# 主函数
main() {
    echo "🔍 tinyproxy代理问题诊断工具"
    echo "================================"
    
    local exit_code=0
    
    check_environment || exit_code=1
    check_tinyproxy_config || exit_code=1
    check_tinyproxy_process || exit_code=1
    test_upstream_connectivity || exit_code=1
    test_local_tinyproxy || exit_code=1
    check_logs
    provide_fix_suggestions
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        log "🎉 所有检查通过！"
    else
        error "❌ 发现问题，请参考上述修复建议"
    fi
    
    return $exit_code
}

main "$@"
