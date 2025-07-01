#!/bin/bash

set -e

echo "🚀 部署SpotLight系统..."

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <deploy_type> [options]"
    echo "部署类型:"
    echo "  main     - 部署主服务器 (API + Hub)"
    echo "  node     - 部署Node节点"
    echo "  all      - 部署完整系统"
    echo ""
    echo "示例:"
    echo "  $0 main                    # 部署主服务器"
    echo "  $0 node 192.168.1.100 4 6  # 部署4个Node，每节点6个会话"
    echo "  $0 all                     # 部署完整系统"
    exit 1
fi

DEPLOY_TYPE=$1

case $DEPLOY_TYPE in
    "main")
        echo "🚀 部署主服务器..."
        
        # 检查Docker
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker未安装"
            exit 1
        fi
        
        # 检查Docker Compose
        if ! command -v docker-compose &> /dev/null; then
            echo "❌ Docker Compose未安装"
            exit 1
        fi
        
        # 创建必要目录
        echo "📁 创建目录..."
        mkdir -p logs
        mkdir -p config
        
        # 构建SpotLight镜像
        echo "🔨 构建SpotLight镜像..."
        docker build -f Dockerfile.spotlight -t spotlight/api:latest .
        
        # 启动主服务
        echo "🚀 启动主服务..."
        docker-compose up -d
        
        # 等待服务启动
        echo "⏳ 等待服务启动..."
        sleep 60
        
        # 检查服务状态
        echo "📊 检查服务状态..."
        docker-compose ps
        
        echo "✅ 主服务器部署完成！"
        echo "📍 API服务: http://localhost:8002"
        echo "📍 Grid Hub: http://localhost:4444"
        ;;
        
    "node")
        if [ $# -lt 2 ]; then
            echo "❌ 需要指定Hub主机地址"
            echo "用法: $0 node <hub_host> [node_count] [max_sessions_per_node]"
            exit 1
        fi
        
        HUB_HOST=$2
        NODE_COUNT=${3:-4}
        MAX_SESSIONS=${4:-6}
        
        echo "🚀 部署Node节点..."
        echo "📍 Hub地址: $HUB_HOST"
        echo "📍 节点数量: $NODE_COUNT"
        echo "📍 每节点最大会话数: $MAX_SESSIONS"
        
        # 运行Node部署脚本
        chmod +x deploy-nodes.sh
        ./deploy-nodes.sh $HUB_HOST $NODE_COUNT $MAX_SESSIONS
        ;;
        
    "all")
        echo "🚀 部署完整系统..."
        
        # 部署主服务器
        $0 main
        
        # 部署Node节点
        echo ""
        echo "请手动部署Node节点："
        echo "  $0 node <主服务器IP> <节点数量> <每节点最大会话数>"
        echo "示例: $0 node 192.168.1.100 4 6"
        ;;
        
    *)
        echo "❌ 无效的部署类型: $DEPLOY_TYPE"
        exit 1
        ;;
esac 