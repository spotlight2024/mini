#!/bin/bash

# tinyproxy代理问题修复脚本
# 针对K8S环境中的常见代理问题提供自动修复

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

# 修复1: 重新生成tinyproxy配置
fix_tinyproxy_config() {
    info "🔧 修复1: 重新生成tinyproxy配置"
    
    if [ -z "$PROXY_HOST" ] || [ -z "$PROXY_PORT" ]; then
        error "❌ 环境变量缺失，无法修复配置"
        echo "请检查K8S部署中的环境变量设置:"
        echo "- PROXY_HOST: ${PROXY_HOST:-未设置}"
        echo "- PROXY_PORT: ${PROXY_PORT:-未设置}"
        return 1
    fi
    
    log "重新执行配置脚本..."
    sudo env PROXY_HOST="$PROXY_HOST" PROXY_PORT="$PROXY_PORT" \
         PROXY_USERNAME="$PROXY_USERNAME" PROXY_PASSWORD="$PROXY_PASSWORD" \
         /opt/tinyproxy-setup/setup-tinyproxy.sh
    
    log "✅ 配置重新生成完成"
}

# 修复2: 重启tinyproxy服务
restart_tinyproxy() {
    info "🔧 修复2: 重启tinyproxy服务"
    
    # 停止现有进程
    if pgrep -f tinyproxy > /dev/null; then
        log "停止现有tinyproxy进程..."
        sudo pkill -f tinyproxy || true
        sleep 2
    fi
    
    # 启动新进程
    log "启动tinyproxy..."
    sudo /usr/bin/tinyproxy -d -c /etc/tinyproxy/tinyproxy.conf &
    sleep 3
    
    # 验证启动
    if pgrep -f tinyproxy > /dev/null; then
        log "✅ tinyproxy已成功重启"
    else
        error "❌ tinyproxy重启失败"
        return 1
    fi
}

# 修复3: 测试连接并提供详细反馈
test_and_feedback() {
    info "🔧 修复3: 测试连接"
    
    echo "1. 测试上游代理连接..."
    if [ -n "$PROXY_HOST" ] && [ -n "$PROXY_PORT" ]; then
        if timeout 10 bash -c "</dev/tcp/${PROXY_HOST}/${PROXY_PORT}" 2>/dev/null; then
            log "✅ 上游代理TCP连接正常"
        else
            error "❌ 上游代理TCP连接失败"
            echo ""
            echo "🔍 网络诊断建议:"
            echo "1. 检查上游代理服务器状态: ${PROXY_HOST}:${PROXY_PORT}"
            echo "2. 验证K8S集群网络策略是否允许出站连接"
            echo "3. 检查防火墙设置"
            return 1
        fi
    fi
    
    echo ""
    echo "2. 测试tinyproxy功能..."
    local test_result=$(timeout 10 curl -x 127.0.0.1:8888 -s --max-time 5 http://httpbin.org/ip 2>&1)
    
    if echo "$test_result" | grep -q "origin"; then
        log "✅ tinyproxy代理功能正常"
        echo "当前出口IP: $(echo "$test_result" | grep -o '"origin": *"[^"]*"' | cut -d'"' -f4)"
    else
        error "❌ tinyproxy代理功能异常"
        echo "响应: $test_result"
        return 1
    fi
}

# 修复4: 更新K8S部署配置建议
suggest_k8s_fixes() {
    info "🔧 修复4: K8S配置建议"
    
    echo ""
    echo "如果问题仍然存在，请检查K8S部署配置:"
    echo ""
    echo "1. 确保环境变量正确设置 (node-deployment.yaml):"
    echo "   env:"
    echo "   - name: PROXY_HOST"
    echo "     value: \"192.168.1.94\""
    echo "   - name: PROXY_PORT"
    echo "     value: \"7879\""
    
    if [ -n "$PROXY_USERNAME" ]; then
        echo "   - name: PROXY_USERNAME"
        echo "     value: \"$PROXY_USERNAME\""
        echo "   - name: PROXY_PASSWORD"
        echo "     value: \"$PROXY_PASSWORD\""
    else
        echo "   # 如果代理需要认证，取消注释以下行:"
        echo "   # - name: PROXY_USERNAME"
        echo "   #   value: \"your_username\""
        echo "   # - name: PROXY_PASSWORD"
        echo "   #   value: \"your_password\""
    fi
    
    echo ""
    echo "2. 重新部署pod:"
    echo "   kubectl delete pod -l app=chrome-node -n selenium-grid"
    echo "   kubectl get pods -n selenium-grid -w"
    
    echo ""
    echo "3. 检查网络策略 (如果存在):"
    echo "   kubectl get networkpolicies -n selenium-grid"
    
    echo ""
    echo "4. 验证集群出站连接:"
    echo "   kubectl run test-pod --rm -i --tty --image=busybox -- /bin/sh"
    echo "   # 在pod中执行: nc -zv ${PROXY_HOST:-192.168.1.94} ${PROXY_PORT:-7879}"
}

# 主修复流程
main() {
    echo "🔧 tinyproxy代理自动修复工具"
    echo "================================"
    
    local exit_code=0
    
    # 显示当前环境
    echo "当前环境信息:"
    echo "- PROXY_HOST: ${PROXY_HOST:-未设置}"
    echo "- PROXY_PORT: ${PROXY_PORT:-未设置}" 
    echo "- PROXY_USERNAME: ${PROXY_USERNAME:-未设置}"
    echo ""
    
    # 执行修复步骤
    fix_tinyproxy_config || exit_code=1
    
    if [ $exit_code -eq 0 ]; then
        restart_tinyproxy || exit_code=1
    fi
    
    if [ $exit_code -eq 0 ]; then
        test_and_feedback || exit_code=1
    fi
    
    suggest_k8s_fixes
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        log "🎉 修复完成！代理应该正常工作了"
    else
        error "❌ 自动修复未完全成功，请参考上述建议手动处理"
    fi
    
    return $exit_code
}

main "$@"
