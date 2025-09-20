#!/bin/bash

# Dynamic proxy IP switching script
# Usage: ./change_proxy.sh <IP> <PORT> <USERNAME> <PASSWORD> [CONTAINER_NAME]

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

# Check parameters
if [ $# -lt 4 ]; then
    error "Usage: $0 <IP> <PORT> <USERNAME> <PASSWORD> [CONTAINER_NAME]"
    error "Example: $0 192.168.1.100 8080 user1 pass1 chrome-node-1"
    exit 1
fi

NEW_IP="$1"
NEW_PORT="$2"
NEW_USER="$3"
NEW_PASS="$4"
CONTAINER="${5:-chrome-node-1}"

log "🔄 Starting proxy IP switch..."
log "   Container: $CONTAINER"
log "   New proxy: $NEW_USER@$NEW_IP:$NEW_PORT"

# Check if container is running
if ! docker compose ps | grep -q "$CONTAINER.*Up"; then
    error "❌ Container $CONTAINER is not running"
    exit 1
fi

# Update docker-compose.yml with new proxy settings
log "📝 Updating docker-compose.yml with new proxy configuration..."
COMPOSE_FILE="docker-compose.yml"

# Update proxy environment variables in docker-compose.yml
sed -i "s/PROXY_HOST=.*/PROXY_HOST=$NEW_IP/" "$COMPOSE_FILE"
sed -i "s/PROXY_PORT=.*/PROXY_PORT=$NEW_PORT/" "$COMPOSE_FILE"
sed -i "s/PROXY_USERNAME=.*/PROXY_USERNAME=$NEW_USER/" "$COMPOSE_FILE"
sed -i "s/PROXY_PASSWORD=.*/PROXY_PASSWORD=$NEW_PASS/" "$COMPOSE_FILE"

log "✅ docker-compose.yml updated with new proxy settings"

# 1. Regenerate tinyproxy configuration
log "📝 Regenerating tinyproxy configuration..."
docker compose exec "$CONTAINER" sudo env \
    PROXY_HOST="$NEW_IP" \
    PROXY_PORT="$NEW_PORT" \
    PROXY_USERNAME="$NEW_USER" \
    PROXY_PASSWORD="$NEW_PASS" \
    /opt/tinyproxy-setup/setup-tinyproxy.sh

if [ $? -ne 0 ]; then
    error "❌ Failed to regenerate tinyproxy configuration"
    exit 1
fi

# 2. Stop existing tinyproxy service
log "🔄 Stopping existing tinyproxy service..."
docker compose exec "$CONTAINER" sudo pkill -f tinyproxy || true
sleep 2

# 3. Apply new proxy configuration by restarting container
log "🚀 Applying new proxy configuration..."
log "   Note: This will restart the container to apply new proxy settings"

# Stop the container
log "🔄 Stopping container..."
docker compose stop "$CONTAINER"

# Start the container with new environment variables
log "🚀 Starting container with new proxy configuration..."
docker compose up -d "$CONTAINER"

# Wait for container to be ready
log "⏳ Waiting for container to be ready..."
sleep 10

# 4. Verify tinyproxy is running
log "🔍 Verifying tinyproxy process..."
# Check if container is running
if ! docker compose ps | grep -q "$CONTAINER.*Up"; then
    error "❌ Container failed to start"
    exit 1
fi

# Check tinyproxy process
if docker compose exec "$CONTAINER" pgrep -f "tinyproxy.*-d" > /dev/null 2>&1; then
    log "✅ tinyproxy process is running"
else
    error "❌ tinyproxy process failed to start"
    # Try to get more information
    log "📋 Checking tinyproxy status:"
    docker compose exec "$CONTAINER" ps aux | grep tinyproxy || echo "No tinyproxy process found"
    exit 1
fi

# 5. Test proxy connectivity
log "🔍 Testing proxy connectivity..."
sleep 2

# Test with multiple attempts
MAX_ATTEMPTS=5
ATTEMPT=1
SUCCESS=false

while [ $ATTEMPT -le $MAX_ATTEMPTS ] && [ "$SUCCESS" = false ]; do
    log "   Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    if docker compose exec "$CONTAINER" curl -s --max-time 10 --proxy http://127.0.0.1:8888 https://ipinfo.io/json > /dev/null 2>&1; then
        SUCCESS=true
        log "✅ Proxy connectivity test passed"
        break
    else
        warn "   Attempt $ATTEMPT failed, retrying..."
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))
    fi
done

if [ "$SUCCESS" = false ]; then
    error "❌ Proxy connectivity test failed after $MAX_ATTEMPTS attempts"
    exit 1
fi

# 6. Get actual exit IP
log "🔍 Getting actual exit IP..."
ACTUAL_IP=$(docker compose exec "$CONTAINER" curl -s --max-time 15 --proxy http://127.0.0.1:8888 https://ipinfo.io/json | python3 -c "import sys,json; print(json.load(sys.stdin)['ip'])" 2>/dev/null || echo "Failed to get IP")

if [ "$ACTUAL_IP" != "Failed to get IP" ]; then
    log "✅ Proxy switch successful!"
    log "   New exit IP: $ACTUAL_IP"
    
    # Get location info
    LOCATION_INFO=$(docker compose exec "$CONTAINER" curl -s --max-time 15 --proxy http://127.0.0.1:8888 https://ipinfo.io/json | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"{data.get('region', 'Unknown')} {data.get('city', 'Unknown')} {data.get('org', 'Unknown')}\")" 2>/dev/null || echo "Unknown location")
    log "   Location: $LOCATION_INFO"
else
    error "❌ Failed to get exit IP"
    exit 1
fi

# 7. Final verification
log "🔍 Final verification..."
if docker compose exec "$CONTAINER" curl -s --max-time 10 --proxy http://127.0.0.1:8888 https://httpbin.org/ip > /dev/null 2>&1; then
    log "✅ Final verification passed"
else
    warn "⚠️  Final verification failed, but proxy might still be working"
fi

log "🎉 Proxy IP switch completed successfully!"
log "   New proxy: $NEW_USER@$NEW_IP:$NEW_PORT"
log "   Exit IP: $ACTUAL_IP"
log "   Container: $CONTAINER"
