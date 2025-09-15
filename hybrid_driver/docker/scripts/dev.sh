#!/bin/bash

# SpotLight Hybrid Driver Docker 开发环境启动脚本

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

echo -e "${GREEN}🚀 启动 SpotLight Hybrid Driver 开发环境...${NC}"

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 进入 Docker 目录
cd "$DOCKER_DIR"

# 创建必要的目录
echo -e "${YELLOW}📁 创建必要的目录...${NC}"
mkdir -p logs data cache

# 启动开发环境
echo -e "${YELLOW}🐳 启动开发环境容器...${NC}"
docker compose -f docker-compose.dev.yml up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 开发环境启动成功！${NC}"
    echo -e "${GREEN}📋 服务状态：${NC}"
    docker compose -f docker-compose.dev.yml ps
    
    echo -e "${GREEN}🌐 服务访问地址：${NC}"
    echo -e "   - API 文档: http://localhost:10001/docs"
    echo -e "   - 健康检查: http://localhost:10001/health"
    echo -e "   - 根路径: http://localhost:10001/"
    
    echo -e "${YELLOW}💡 开发环境特性：${NC}"
    echo -e "   - 代码热重载已启用"
    echo -e "   - 源代码目录已挂载"
    echo -e "   - 调试日志已启用"
    
    echo -e "${YELLOW}💡 管理命令：${NC}"
    echo -e "   - 查看日志: docker compose -f docker-compose.dev.yml logs -f"
    echo -e "   - 停止服务: docker compose -f docker-compose.dev.yml down"
    echo -e "   - 重启服务: docker compose -f docker-compose.dev.yml restart"
else
    echo -e "${RED}❌ 开发环境启动失败！${NC}"
    echo -e "${YELLOW}🔍 查看错误日志：${NC}"
    docker compose -f docker-compose.dev.yml logs
    exit 1
fi
