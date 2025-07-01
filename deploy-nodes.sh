#!/bin/bash

set -e

echo "🚀 部署SpotLight Node节点..."

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <hub_host> [node_count] [max_sessions_per_node]"
    echo "示例: $0 192.168.1.100 4 6"
    exit 1
fi

HUB_HOST=$1
NODE_COUNT=${2:-4}
MAX_SESSIONS_PER_NODE=${3:-6}

echo "📍 Hub地址: $HUB_HOST"
echo "📍 节点数量: $NODE_COUNT"
echo "📍 每节点最大会话数: $MAX_SESSIONS_PER_NODE"

# 创建网络
docker network create spotlight-network 2>/dev/null || true

# 停止并删除现有节点
echo "🧹 清理现有节点..."
docker ps -q --filter "name=selenium-node" | xargs -r docker stop
docker ps -aq --filter "name=selenium-node" | xargs -r docker rm

# 启动Node节点
for i in $(seq 1 $NODE_COUNT); do
    echo "🚀 启动Node节点 $i..."
    
    docker run -d \
        --name "selenium-node-chrome-$i" \
        --network spotlight-network \
        -e "SE_EVENT_BUS_HOST=$HUB_HOST" \
        -e "SE_EVENT_BUS_PUBLISH_PORT=4442" \
        -e "SE_EVENT_BUS_SUBSCRIBE_PORT=4443" \
        -e "SE_NODE_MAX_SESSIONS=$MAX_SESSIONS_PER_NODE" \
        -e "SE_NODE_OVERRIDE_MAX_SESSIONS=true" \
        -e "SE_NODE_SESSION_TIMEOUT=300" \
        -e "SE_NODE_OVERRIDE_MAX_SESSIONS=true" \
        --shm-size 1gb \
        --restart unless-stopped \
        selenium/node-chrome:latest
    
    echo "✅ Node节点 $i 启动成功"
done

echo "🎉 所有Node节点部署完成！"
echo ""
echo "📍 节点状态："
docker ps --filter "name=selenium-node" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "🔍 检查Grid状态："
sleep 10
curl -s "http://$HUB_HOST:4444/wd/hub/status" | jq '.value.nodes | length' 2>/dev/null || echo "Grid状态检查失败" 