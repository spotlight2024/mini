#!/bin/bash

# SpotLight Hybrid Driver Docker 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}🚀 启动 SpotLight Hybrid Driver 服务...${NC}"

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 进入 Docker 目录
cd "$DOCKER_DIR"

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  未找到 .env 文件，使用默认配置${NC}"
    if [ -f "env.example" ]; then
        echo -e "${BLUE}💡 提示：可以复制 env.example 为 .env 来自定义配置${NC}"
        echo -e "   cp env.example .env"
    fi
fi

# 创建必要的目录
echo -e "${YELLOW}📁 创建必要的目录...${NC}"
mkdir -p logs data cache

# 启动服务
echo -e "${YELLOW}🐳 启动 Docker 容器...${NC}"
docker compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 服务启动成功！${NC}"
    echo -e "${GREEN}📋 服务状态：${NC}"
    docker compose ps
    
    echo -e "${GREEN}🌐 服务访问地址：${NC}"
    echo -e "   - API 文档: http://localhost:10001/docs"
    echo -e "   - 健康检查: http://localhost:10001/health"
    echo -e "   - 根路径: http://localhost:10001/"
    
    echo -e "${YELLOW}💡 管理命令：${NC}"
    echo -e "   - 查看日志: docker compose logs -f"
    echo -e "   - 停止服务: docker compose down"
    echo -e "   - 重启服务: docker compose restart"
else
    echo -e "${RED}❌ 服务启动失败！${NC}"
    echo -e "${YELLOW}🔍 查看错误日志：${NC}"
    docker compose logs
    exit 1
fi
