#!/bin/bash

# Unified starter for SpotLight Hybrid Driver API
# Usage:
#   scripts/spotlight.sh dev   [--host 127.0.0.1] [--port 10001]
#   scripts/spotlight.sh serve [--host 0.0.0.0] [--port 10001] [--workers 2] [--log-level info]
#   scripts/spotlight.sh docker-dev [--host 0.0.0.0] [--port 10001] [--log-level debug]
#   scripts/spotlight.sh docker [--host 0.0.0.0] [--port 10001] [--log-level info]
#   scripts/spotlight.sh build [--tag TAG] [--port PORT]
#   scripts/spotlight.sh deploy [--tag TAG] [--port PORT]
#   scripts/spotlight.sh update [--tag TAG] [--port PORT]
#   scripts/spotlight.sh status
#   scripts/spotlight.sh logs

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
IMAGE_NAME="spotlight-api"
DEFAULT_TAG="latest"

# 获取命令
CMD="${1:-}"
shift 2>/dev/null || true

# 解析环境变量
API_HOST_DEFAULT="${API_HOST:-}"
API_PORT_DEFAULT="${API_PORT:-}"
LOG_LEVEL_DEFAULT="${LOG_LEVEL:-}"

# Check if Docker is running
check_docker() {
  if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
    exit 1
  fi
}

# 本地开发模式
run_dev() {
  local host="${HOST:-${API_HOST_DEFAULT:-127.0.0.1}}"
  local port="${PORT:-${API_PORT_DEFAULT:-10001}}"
  
  echo -e "${BLUE}[DEV] Starting SpotLight API in development mode${NC}"
  echo "  Host: ${host}"
  echo "  Port: ${port}"
  echo "  Auto-reload: enabled"
  
  python -m uvicorn hybrid_driver.server_optimized:app \
    --host "${host}" \
    --port "${port}" \
    --reload
}

# 本地生产模式
run_serve() {
  local host="${HOST:-${API_HOST_DEFAULT:-0.0.0.0}}"
  local port="${PORT:-${API_PORT_DEFAULT:-10001}}"
  local workers="${WORKERS:-2}"
  local level="${LOG_LEVEL:-${LOG_LEVEL_DEFAULT:-info}}"
  
  echo -e "${BLUE}[SERVE] Starting SpotLight API in production mode${NC}"
  echo "  Host: ${host}"
  echo "  Port: ${port}"
  echo "  Workers: ${workers}"
  echo "  Log Level: ${level}"
  
  python -m uvicorn hybrid_driver.server_optimized:app \
    --host "${host}" \
    --port "${port}" \
    --workers "${workers}" \
    --log-level "${level}"
}

# Docker开发模式（代码挂载，支持热重载）
run_docker_dev() {
  check_docker
  
  local host="${HOST:-${API_HOST_DEFAULT:-0.0.0.0}}"
  local port="${PORT:-${API_PORT_DEFAULT:-10001}}"
  local level="${LOG_LEVEL:-${LOG_LEVEL_DEFAULT:-debug}}"
  
  echo -e "${BLUE}[DOCKER-DEV] Starting SpotLight API in Docker (development mode)${NC}"
  echo "  Host: ${host}"
  echo "  Port: ${port}"
  echo "  Log Level: ${level}"
  echo "  Code mounted for hot reload"
  
  # Set environment variables for docker-compose
  export API_HOST="${host}"
  export API_PORT="${port}"
  export LOG_LEVEL="${level}"
  export ENVIRONMENT="development"
  
  # Start development container
  docker compose -f docker-compose.dev.yml up -d
  
  echo ""
  echo -e "${GREEN}✅ Development container started!${NC}"
  echo "🌐 Service: http://localhost:${port}"
  echo "📚 API Docs: http://localhost:${port}/docs"
  echo "💚 Health: http://localhost:${port}/health"
  echo ""
  echo "💡 Tips:"
  echo "  - Code changes will auto-reload"
  echo "  - View logs: docker compose -f docker-compose.dev.yml logs -f"
  echo "  - Stop: docker compose -f docker-compose.dev.yml down"
}

# Docker生产模式（代码打包）
run_docker() {
  check_docker
  
  local host="${HOST:-${API_HOST_DEFAULT:-0.0.0.0}}"
  local port="${PORT:-${API_PORT_DEFAULT:-10001}}"
  local level="${LOG_LEVEL:-${LOG_LEVEL_DEFAULT:-info}}"
  
  echo -e "${BLUE}[DOCKER] Starting SpotLight API in Docker (production mode)${NC}"
  echo "  Host: ${host}"
  echo "  Port: ${port}"
  echo "  Log Level: ${level}"
  
  # Set environment variables for docker-compose
  export API_HOST="${host}"
  export API_PORT="${port}"
  export LOG_LEVEL="${level}"
  export ENVIRONMENT="production"
  
  # Start production container
  docker compose -f docker-compose.api.yml up -d
  
  echo ""
  echo -e "${GREEN}✅ Production container started!${NC}"
  echo "🌐 Service: http://localhost:${port}"
  echo "📚 API Docs: http://localhost:${port}/docs"
  echo "💚 Health: http://localhost:${port}/health"
  echo ""
  echo "💡 Tips:"
  echo "  - View logs: docker compose -f docker-compose.api.yml logs -f"
  echo "  - Stop: docker compose -f docker-compose.api.yml down"
}

# 构建生产镜像（暂时留口子）
build_image() {
  local tag="${1:-latest}"
  
  echo -e "${YELLOW}[BUILD] Building production image...${NC}"
  echo "  Tag: ${tag}"
  echo "  Status: 🚧 功能开发中，暂时不可用"
  echo ""
  echo "💡 提示: 生产环境构建功能正在开发中，敬请期待！"
  
  # TODO: 实现生产镜像构建逻辑
  # docker build --build-arg VERSION="$tag" -t "$IMAGE_NAME:$tag" -f Dockerfile.spotlight .
}

# 部署到生产环境（暂时留口子）
deploy_production() {
  local tag="${1:-latest}"
  local port="${2:-10001}"
  
  echo -e "${YELLOW}[DEPLOY] Deploying to production...${NC}"
  echo "  Tag: ${tag}"
  echo "  Port: ${port}"
  echo "  Status: 🚧 功能开发中，暂时不可用"
  echo ""
  echo "💡 提示: 生产环境部署功能正在开发中，敬请期待！"
  
  # TODO: 实现生产环境部署逻辑
}

# 更新代码并部署（暂时留口子）
update_and_deploy() {
  local tag="${1:-latest}"
  local port="${2:-10001}"
  
  echo -e "${YELLOW}[UPDATE] Updating code and deploying...${NC}"
  echo "  Tag: ${tag}"
  echo "  Port: ${port}"
  echo "  Status: 🚧 功能开发中，暂时不可用"
  echo ""
  echo "💡 提示: 生产环境更新部署功能正在开发中，敬请期待！"
  
  # TODO: 实现更新部署逻辑
}

# 查看部署状态
show_status() {
  echo -e "${BLUE}[STATUS] SpotLight deployment status:${NC}"
  
  # 检查本地服务
  echo ""
  echo "🖥️  Local Services:"
  if curl -f "http://localhost:10001/health" >/dev/null 2>&1; then
    echo -e "  ✅ Port 10001: Running"
  else
    echo -e "  ❌ Port 10001: Not running"
  fi
  
  # 检查Docker服务
  echo ""
  echo "🐳 Docker Services:"
  if docker compose -f docker-compose.api.yml ps | grep -q "Up"; then
    echo -e "  ✅ Production: Running"
  else
    echo -e "  ❌ Production: Not running"
  fi
  
  if docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo -e "  ✅ Development: Running"
  else
    echo -e "  ❌ Development: Not running"
  fi
  
  # 显示镜像信息
  echo ""
  echo "📦 Docker Images:"
  docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" 2>/dev/null || echo "  No images found"
}

# 查看日志
show_logs() {
  local service="${1:-}"
  
  if [[ -z "$service" ]]; then
    echo -e "${BLUE}[LOGS] Available log sources:${NC}"
    echo "  local     - Local service logs (if running)"
    echo "  docker    - Production container logs"
    echo "  docker-dev - Development container logs"
    echo ""
    echo "Usage: $0 logs [local|docker|docker-dev]"
    return
  fi
  
  case "$service" in
    local)
      echo -e "${BLUE}[LOGS] Local service logs:${NC}"
      echo "💡 提示: 本地服务日志显示在启动终端中"
      ;;
    docker)
      echo -e "${BLUE}[LOGS] Production container logs:${NC}"
      docker compose -f docker-compose.api.yml logs -f spotlight-api
      ;;
    docker-dev)
      echo -e "${BLUE}[LOGS] Development container logs:${NC}"
      docker compose -f docker-compose.dev.yml logs -f spotlight-api-dev
      ;;
    *)
      echo -e "${RED}Error: Unknown service '$service'${NC}"
      echo "Available: local, docker, docker-dev"
      exit 1
      ;;
  esac
}

# 显示帮助信息
show_help() {
  cat <<'EOF'
SpotLight 统一启动脚本

用法: scripts/spotlight.sh [命令] [选项]

🚀 服务启动命令:
  dev          - 本地开发模式 (热重载)
  serve        - 本地生产模式 (多进程)
  docker-dev   - Docker开发模式 (代码挂载，热重载)
  docker       - Docker生产模式 (代码打包)

🔧 生产环境管理命令 (开发中):
  build        - 构建生产镜像
  deploy       - 部署到生产环境
  update       - 更新代码并部署
  status       - 查看部署状态
  logs         - 查看服务日志

📋 选项:
  --host HOST      指定主机地址
  --port PORT      指定端口号
  --workers N      指定工作进程数 (仅serve模式)
  --log-level LEVEL 指定日志级别
  --tag TAG        指定版本标签 (仅生产命令)

🌍 环境变量:
  API_HOST         默认主机地址
  API_PORT         默认端口号
  LOG_LEVEL        默认日志级别

💡 使用示例:
  # 开发环境
  ./scripts/spotlight.sh dev
  ./scripts/spotlight.sh docker-dev --port 10002
  
  # 生产环境
  ./scripts/spotlight.sh serve --port 10001 --workers 4
  ./scripts/spotlight.sh docker --port 10001
  
  # 生产管理 (开发中)
  ./scripts/spotlight.sh build --tag v1.0.0
  ./scripts/spotlight.sh status
  ./scripts/spotlight.sh logs docker

📚 更多信息:
  - 快速启动: docs/quick-start.md
  - 详细部署: docs/deployment-guide.md
EOF
}

# 主函数
case "${CMD}" in
  # 服务启动命令
  dev) run_dev;;
  serve|prod|start) run_serve;;
  docker-dev) run_docker_dev;;
  docker) run_docker;;
  
  # 生产环境管理命令 (开发中)
  build) 
    tag="${1:-latest}"
    port="${2:-10001}"
    build_image "$tag"
    ;;
  deploy)
    tag="${1:-latest}"
    port="${2:-10001}"
    deploy_production "$tag" "$port"
    ;;
  update)
    tag="${1:-latest}"
    port="${2:-10001}"
    update_and_deploy "$tag" "$port"
    ;;
  status) show_status;;
  logs) show_logs "${1:-}";;
  
  # 帮助和错误处理
  help|--help|-h) show_help;;
  "")
    echo -e "${RED}Error: Please specify a command${NC}"
    echo ""
    show_help
    exit 1
    ;;
  *)
    echo -e "${RED}Error: Unknown command '${CMD}'${NC}"
    echo ""
    show_help
    exit 1
    ;;
esac


