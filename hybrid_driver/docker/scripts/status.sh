#!/bin/bash

# SpotLight Hybrid Driver Docker 状态检查脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}📊 SpotLight Hybrid Driver 服务状态${NC}"
echo -e "${BLUE}================================${NC}"

# 进入 Docker 目录
cd "$DOCKER_DIR"

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行${NC}"
    exit 1
fi

# 显示容器状态
echo -e "${YELLOW}🐳 容器状态：${NC}"
docker compose ps

echo ""

# 显示资源使用情况
echo -e "${YELLOW}💻 资源使用情况：${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" $(docker compose ps -q) 2>/dev/null || echo "暂无运行中的容器"

echo ""

# 检查服务健康状态
echo -e "${YELLOW}🏥 健康检查：${NC}"
if curl -s -f http://localhost:10001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API 服务健康${NC}"
    echo -e "${GREEN}🌐 服务地址: http://localhost:10001${NC}"
    echo -e "${GREEN}📚 API 文档: http://localhost:10001/docs${NC}"
else
    echo -e "${RED}❌ API 服务不可用${NC}"
fi

echo ""

# 显示日志信息
echo -e "${YELLOW}📝 最近日志：${NC}"
docker compose logs --tail=10
