#!/bin/bash

# Selenium节点启动脚本
# 支持动态扩容和节点管理

set -e

# 配置变量
HUB_HOST=${SELENIUM_HUB_HOST:-selenium-hub}
HUB_PUBLISH_PORT=${SELENIUM_HUB_PUBLISH_PORT:-4442}
HUB_SUBSCRIBE_PORT=${SELENIUM_HUB_SUBSCRIBE_PORT:-4443}
NODE_COUNT=${SELENIUM_NODE_COUNT:-2}
NODE_IMAGE=${SELENIUM_NODE_IMAGE:-selenium/node-chrome:4.33.0-20250606}
NETWORK_NAME=${NETWORK_NAME:-spotlight-network}

echo "启动 Selenium 节点服务..."
echo "Hub地址: $HUB_HOST:$HUB_PUBLISH_PORT"
echo "节点数量: $NODE_COUNT"
echo "节点镜像: $NODE_IMAGE"

# 检查网络是否存在
if ! docker network ls | grep -q "$NETWORK_NAME"; then
    echo "创建网络: $NETWORK_NAME"
    docker network create "$NETWORK_NAME"
fi

# 停止并删除现有节点
echo "清理现有节点..."
docker ps -a --filter "name=selenium-node-" --format "{{.Names}}" | xargs -r docker rm -f

# 启动新节点
for i in $(seq 1 $NODE_COUNT); do
    NODE_NAME="selenium-node-chrome-$i"
    echo "启动节点: $NODE_NAME"
    
    docker run -d \
        --name "$NODE_NAME" \
        --network "$NETWORK_NAME" \
        -e SE_EVENT_BUS_HOST="$HUB_HOST" \
        -e SE_EVENT_BUS_PUBLISH_PORT="$HUB_PUBLISH_PORT" \
        -e SE_EVENT_BUS_SUBSCRIBE_PORT="$HUB_SUBSCRIBE_PORT" \
        -e SE_NODE_MAX_SESSIONS=4 \
        -e SE_NODE_OVERRIDE_MAX_SESSIONS=true \
        -e SE_NODE_SESSION_TIMEOUT=300 \
        -e SE_NODE_REGISTER_CYCLE=10000 \
        -e SE_NODE_REGISTER_PERIOD=10000 \
        -e SE_NODE_HOST="$NODE_NAME" \
        -e SE_NODE_PORT=5555 \
        -v /dev/shm:/dev/shm \
        --restart unless-stopped \
        --memory=2g \
        --cpus=1.0 \
        "$NODE_IMAGE"
    
    echo "节点 $NODE_NAME 启动完成"
done

echo "所有节点启动完成！"
echo "当前运行的节点:"
docker ps --filter "name=selenium-node-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 等待节点注册
echo "等待节点注册到Hub..."
sleep 10

# 检查Hub状态
echo "Hub状态:"
curl -s "http://$HUB_HOST:4444/wd/hub/status" | python3 -m json.tool 2>/dev/null || echo "Hub状态检查失败" 