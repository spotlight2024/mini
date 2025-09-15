#!/bin/bash

# SpotLight Hybrid Driver Docker 停止脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}🛑 停止 SpotLight Hybrid Driver 服务...${NC}"

# 进入 Docker 目录
cd "$DOCKER_DIR"

# 停止服务
docker compose down

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 服务已停止！${NC}"
else
    echo -e "${RED}❌ 停止服务时出现错误！${NC}"
    exit 1
fi

# 询问是否清理数据
echo -e "${YELLOW}🗑️  是否清理数据？(y/N)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🧹 清理数据...${NC}"
    docker compose down -v
    rm -rf logs/* data/* cache/*
    echo -e "${GREEN}✅ 数据已清理！${NC}"
fi
