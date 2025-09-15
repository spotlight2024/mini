#!/bin/bash

# SpotLight Hybrid Driver Docker 构建脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$DOCKER_DIR")"

echo -e "${GREEN}🚀 开始构建 SpotLight Hybrid Driver Docker 镜像...${NC}"

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 进入项目根目录
cd "$PROJECT_ROOT"

# 构建镜像
echo -e "${YELLOW}📦 构建 Docker 镜像...${NC}"
docker build -f hybrid_driver/docker/Dockerfile -t spotlight-hybrid-driver:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker 镜像构建成功！${NC}"
    echo -e "${GREEN}📋 镜像信息：${NC}"
    docker images | grep spotlight-hybrid-driver
else
    echo -e "${RED}❌ Docker 镜像构建失败！${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 构建完成！${NC}"
echo -e "${YELLOW}💡 提示：${NC}"
echo -e "   - 使用 'docker-compose up -d' 启动服务"
echo -e "   - 使用 'docker-compose -f docker-compose.dev.yml up -d' 启动开发环境"
echo -e "   - 访问 http://localhost:10001 查看 API 文档"
