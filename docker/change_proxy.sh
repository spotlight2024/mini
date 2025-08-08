#!/bin/bash
"""
动态更换代理IP脚本
用法: ./change_proxy.sh <新IP> <端口> <用户名> <密码>
"""

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

if [ $# -lt 4 ]; then
    error "用法: $0 <IP> <端口> <用户名> <密码> [容器名]"
    error "示例: $0 192.168.1.100 8080 user1 pass1 chrome-node-1"
    exit 1
fi

NEW_IP="$1"
NEW_PORT="$2"
NEW_USER="$3"
NEW_PASS="$4"
CONTAINER="${5:-chrome-node-1}"

log "🔄 开始更换代理IP..."
log "   容器: $CONTAINER"
log "   新代理: $NEW_USER@$NEW_IP:$NEW_PORT"

# 1. 重新生成tinyproxy配置
log "📝 重新生成tinyproxy配置..."
docker compose exec "$CONTAINER" sudo env \
    PROXY_HOST="$NEW_IP" \
    PROXY_PORT="$NEW_PORT" \
    PROXY_USERNAME="$NEW_USER" \
    PROXY_PASSWORD="$NEW_PASS" \
    /opt/tinyproxy-setup/setup-tinyproxy.sh

# 2. 重启tinyproxy
log "🔄 重启tinyproxy服务..."
docker compose exec "$CONTAINER" sudo pkill tinyproxy || true
sleep 2
docker compose exec "$CONTAINER" sudo /usr/bin/tinyproxy -d -c /etc/tinyproxy/tinyproxy.conf &

# 3. 验证新代理
log "🔍 验证新代理IP..."
sleep 3
NEW_ACTUAL_IP=$(docker compose exec "$CONTAINER" curl -s https://qifu-api.baidubce.com/ip/local/geo/v1/district | python3 -c "import sys,json; print(json.load(sys.stdin)['ip'])" 2>/dev/null || echo "获取失败")

if [ "$NEW_ACTUAL_IP" != "获取失败" ]; then
    log "✅ 代理更换成功！"
    log "   新出口IP: $NEW_ACTUAL_IP"
else
    error "❌ 代理更换失败，请检查配置"
    exit 1
fi

log "🎉 代理IP更换完成！"
