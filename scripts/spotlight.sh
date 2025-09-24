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

POETRY_BIN="${POETRY_BIN:-poetry}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

# 智能环境检测和启动方式选择
smart_environment_setup() {
  echo -e "${BLUE}🔍 智能环境检测...${NC}"
  
  # 检测Python版本和可用性
  local python_cmd=""
  if command -v python3 &> /dev/null; then
    python_cmd="python3"
    echo -e "${GREEN}✅ 检测到Python3: $(python3 --version)${NC}"
  elif command -v python &> /dev/null; then
    python_cmd="python"
    echo -e "${GREEN}✅ 检测到Python: $(python --version)${NC}"
  else
    echo -e "${RED}❌ 未检测到Python环境${NC}"
    echo -e "${YELLOW}💡 建议: 安装Python 3.8+ 或使用Docker模式${NC}"
    return 1
  fi
  
  # 检测Docker可用性
  local docker_available=false
  if command -v docker &> /dev/null && docker info &> /dev/null; then
    docker_available=true
    echo -e "${GREEN}✅ Docker环境可用${NC}"
  else
    echo -e "${YELLOW}⚠️  Docker环境不可用${NC}"
  fi
  
  # 检测虚拟环境
  local venv_active=false
  if [[ "${VIRTUAL_ENV:-}" != "" ]]; then
    venv_active=true
    echo -e "${GREEN}✅ 虚拟环境已激活: $VIRTUAL_ENV${NC}"
  else
    echo -e "${YELLOW}⚠️  未检测到虚拟环境${NC}"
  fi
  
  # 检测Python依赖
  local python_ready=false
  local missing_deps=()
  
  # 检查关键依赖包
  if ! $python_cmd -c "import fastapi" 2>/dev/null; then
    missing_deps+=("fastapi")
  fi
  
  if ! $python_cmd -c "import uvicorn" 2>/dev/null; then
    missing_deps+=("uvicorn")
  fi
  
  if ! $python_cmd -c "import selenium" 2>/dev/null; then
    missing_deps+=("selenium")
  fi
  
  if [ ${#missing_deps[@]} -eq 0 ]; then
    python_ready=true
    echo -e "${GREEN}✅ Python环境就绪${NC}"
  else
    echo -e "${YELLOW}⚠️  Python环境缺少依赖: ${missing_deps[*]}${NC}"
    if command -v "$POETRY_BIN" &> /dev/null && [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
      echo -e "${BLUE}💡 检测到Poetry项目，将使用Poetry创建依赖环境${NC}"
      python_ready=true
      local poetry_python="$PROJECT_ROOT/.venv/bin/python"
      if [ -x "$poetry_python" ]; then
        python_cmd="$poetry_python"
        venv_active=true
      fi
    fi
  fi
  
  # 智能选择启动方式
  if [ "$python_ready" = true ] && [ "$venv_active" = true ]; then
    echo -e "${GREEN}🎯 选择: 本地Python虚拟环境启动${NC}"
    return 0  # 本地Python虚拟环境
  elif [ "$python_ready" = true ]; then
    echo -e "${GREEN}🎯 选择: 本地Python环境启动${NC}"
    return 0  # 本地Python
  elif [ "$docker_available" = true ]; then
    echo -e "${GREEN}🎯 选择: Docker环境启动${NC}"
    return 2  # Docker
  else
    echo -e "${RED}❌ 无法找到可用的启动环境${NC}"
    return 1  # 失败
  fi
}

# 智能Python环境管理和依赖安装
setup_python_environment() {
  echo -e "${BLUE}🐍 使用Poetry管理Python环境...${NC}"

  if ! command -v "$POETRY_BIN" &> /dev/null; then
    echo -e "${RED}❌ 未检测到Poetry，请参考 https://python-poetry.org/docs/ 安装${NC}"
    return 1
  fi

  if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo -e "${RED}❌ 未找到pyproject.toml，无法安装依赖${NC}"
    return 1
  fi

  echo -e "${BLUE}📘 Poetry 安装/同步依赖...${NC}"
  pushd "$PROJECT_ROOT" > /dev/null
  if "$POETRY_BIN" install --with dev --no-root --no-interaction; then
    popd > /dev/null
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
    return 0
  fi
  popd > /dev/null

  echo -e "${RED}❌ Poetry 安装依赖失败${NC}"
  return 1
}

# 检查端口占用
check_port_availability() {
  local port="$1"
  
  if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
    echo -e "${YELLOW}⚠️  端口 ${port} 已被占用${NC}"
    
    # 查找占用端口的进程
    local pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
    
    if [ -n "$pid" ]; then
      echo -e "${BLUE}🔍 占用进程ID: ${pid}${NC}"
      echo -e "${YELLOW}是否要停止该进程？(y/N)${NC}"
      read -r response
      
      if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🛑 正在停止进程 ${pid}...${NC}"
        kill -9 "$pid" 2>/dev/null
        sleep 2
        
        # 再次检查端口
        if ! netstat -tlnp 2>/dev/null | grep -q ":$port "; then
          echo -e "${GREEN}✅ 端口 ${port} 已释放${NC}"
        else
          echo -e "${RED}❌ 端口 ${port} 仍被占用，请手动处理${NC}"
          exit 1
        fi
      else
        echo -e "${RED}❌ 端口被占用，无法启动服务${NC}"
        exit 1
      fi
    fi
  else
    echo -e "${GREEN}✅ 端口 ${port} 可用${NC}"
  fi
}

# 本地开发模式
run_dev() {
  local host="${HOST:-${API_HOST_DEFAULT:-0.0.0.0}}"
  local port="${PORT:-${API_PORT_DEFAULT:-10001}}"
  
  echo -e "${BLUE}[DEV] Starting SpotLight API in development mode${NC}"
  echo "  Host: ${host}"
  echo "  Port: ${port}"
  echo "  Auto-reload: enabled"
  
  # 智能环境检测
  smart_environment_setup
  local env_result=$?
  
  case $env_result in
    0)  # 本地Python环境
      echo -e "${GREEN}🎯 使用本地Python环境启动${NC}"
      if ! setup_python_environment; then
        echo -e "${RED}❌ 依赖安装失败，无法启动服务${NC}"
        exit 1
      fi
      check_port_availability "$port"
      
      echo -e "${BLUE}🚀 启动服务...${NC}"
      
      # 后台启动服务
      nohup "$POETRY_BIN" run uvicorn hybrid_driver.server_optimized:app \
        --host "${host}" \
        --port "${port}" \
        --reload > uvicorn.log 2>&1 &
      
      local pid=$!
      sleep 2
      
      # 检查服务是否成功启动
      if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ 服务已成功启动在后台${NC}"
        echo "🌐 Service: http://${host}:${port}"
        echo "📚 API Docs: http://${host}:${port}/docs"
        echo "💚 Health: http://${host}:${port}/health"
        echo "📝 Logs: tail -f uvicorn.log"
        echo "🛑 Stop: kill $pid"
        echo ""
        echo "💡 Tips:"
        echo "  - 代码修改会自动重载"
        echo "  - 查看日志: tail -f uvicorn.log"
        echo "  - 停止服务: kill $pid"
      else
        echo -e "${RED}❌ 服务启动失败，请检查日志: uvicorn.log${NC}"
        exit 1
      fi
      ;;
    2)  # Docker环境
      echo -e "${GREEN}🎯 使用Docker环境启动${NC}"
      run_docker_dev
      ;;
    *)  # 失败
      echo -e "${RED}❌ 环境检测失败，无法启动服务${NC}"
      exit 1
      ;;
  esac
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
  
  # 智能环境检测
  smart_environment_setup
  local env_result=$?
  
  case $env_result in
    0)  # 本地Python环境
      echo -e "${GREEN}🎯 使用本地Python环境启动${NC}"
      if ! setup_python_environment; then
        echo -e "${RED}❌ 依赖安装失败，无法启动服务${NC}"
        exit 1
      fi
      check_port_availability "$port"
      
      echo -e "${BLUE}🚀 启动服务...${NC}"
      
      # 后台启动服务
      nohup "$POETRY_BIN" run uvicorn hybrid_driver.server_optimized:app \
        --host "${host}" \
        --port "${port}" \
        --workers "${workers}" \
        --log-level "${level}" > uvicorn.log 2>&1 &
      
      local pid=$!
      sleep 2
      
      # 检查服务是否成功启动
      if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ 服务已成功启动在后台${NC}"
        echo "🌐 Service: http://${host}:${port}"
        echo "📚 API Docs: http://${host}:${port}/docs"
        echo "💚 Health: http://${host}:${port}/health"
        echo "📝 Logs: tail -f uvicorn.log"
        echo "🛑 Stop: kill $pid"
        echo ""
        echo "💡 Tips:"
        echo "  - 多进程模式: ${workers} workers"
        echo "  - 查看日志: tail -f uvicorn.log"
        echo "  - 停止服务: kill $pid"
      else
        echo -e "${RED}❌ 服务启动失败，请检查日志: uvicorn.log${NC}"
        exit 1
      fi
      ;;
    2)  # Docker环境
      echo -e "${GREEN}🎯 使用Docker环境启动${NC}"
      run_docker
      ;;
    *)  # 失败
      echo -e "${RED}❌ 环境检测失败，无法启动服务${NC}"
      exit 1
      ;;
  esac
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

# 构建生产镜像
build_image() {
  local tag="${1:-latest}"
  local context="${2:-.}"
  
  echo -e "${BLUE}[BUILD] Building SpotLight production image...${NC}"
  echo "  Tag: ${tag}"
  echo "  Context: ${context}"
  echo "  Dockerfile: Dockerfile.spotlight"
  
  # 检查Dockerfile是否存在
  if [[ ! -f "Dockerfile.spotlight" ]]; then
    echo -e "${YELLOW}⚠️  Dockerfile.spotlight 不存在，正在创建...${NC}"
    create_spotlight_dockerfile
  fi
  
  # 检查构建上下文
  if [[ ! -d "$context" ]]; then
    echo -e "${RED}❌ 构建上下文目录不存在: ${context}${NC}"
    exit 1
  fi
  
  # 构建镜像
  echo -e "${BLUE}🔨 开始构建镜像...${NC}"
  if docker build \
    --build-arg VERSION="$tag" \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --build-arg GIT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
    -t "$IMAGE_NAME:$tag" \
    -f Dockerfile.spotlight \
    "$context"; then
    
    echo -e "${GREEN}✅ 镜像构建成功！${NC}"
    echo "  Image: $IMAGE_NAME:$tag"
    echo "  Size: $(docker images "$IMAGE_NAME:$tag" --format "{{.Size}}")"
    
    # 显示镜像信息
    echo ""
    echo "📦 镜像详情:"
    docker images "$IMAGE_NAME:$tag" --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}"
    
    # 可选：推送到镜像仓库
    if [[ -n "${DOCKER_REGISTRY:-}" ]]; then
      echo ""
      echo -e "${YELLOW}💡 提示: 检测到镜像仓库配置，可以使用以下命令推送镜像:${NC}"
      echo "  docker tag $IMAGE_NAME:$tag $DOCKER_REGISTRY/$IMAGE_NAME:$tag"
      echo "  docker push $DOCKER_REGISTRY/$IMAGE_NAME:$tag"
    fi
  else
    echo -e "${RED}❌ 镜像构建失败${NC}"
    exit 1
  fi
}

# 部署到生产环境
deploy_production() {
  local tag="${1:-latest}"
  local port="${2:-10001}"
  local env_file="${3:-.env.production}"
  
  echo -e "${BLUE}[DEPLOY] Deploying SpotLight to production...${NC}"
  echo "  Tag: ${tag}"
  echo "  Port: ${port}"
  echo "  Environment: ${env_file}"
  
  # 检查镜像是否存在
  if ! docker images "$IMAGE_NAME:$tag" | grep -q "$tag"; then
    echo -e "${YELLOW}⚠️  镜像 $IMAGE_NAME:$tag 不存在，正在构建...${NC}"
    build_image "$tag"
  fi
  
  # 检查生产环境配置文件
  if [[ ! -f "$env_file" ]]; then
    echo -e "${YELLOW}⚠️  生产环境配置文件不存在，正在创建默认配置...${NC}"
    create_production_env_file "$env_file"
  fi
  
  # 设置环境变量
  export API_PORT="$port"
  export ENVIRONMENT="production"
  export IMAGE_TAG="$tag"
  
  # 停止现有服务
  echo -e "${BLUE}🛑 停止现有生产服务...${NC}"
  docker compose -f docker-compose.api.yml down 2>/dev/null || true
  
  # 启动生产服务
  echo -e "${BLUE}🚀 启动生产服务...${NC}"
  if docker compose -f docker-compose.api.yml up -d; then
    echo -e "${GREEN}✅ 生产环境部署成功！${NC}"
    echo ""
    echo "🌐 Service: http://localhost:${port}"
    echo "📚 API Docs: http://localhost:${port}/docs"
    echo "💚 Health: http://localhost:${port}/health"
    echo ""
    echo "💡 管理命令:"
    echo "  - 查看状态: $0 status"
    echo "  - 查看日志: $0 logs docker"
    echo "  - 停止服务: docker compose -f docker-compose.api.yml down"
    echo "  - 重启服务: docker compose -f docker-compose.api.yml restart"
    
    # 等待服务启动
    echo ""
    echo -e "${BLUE}⏳ 等待服务启动...${NC}"
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
      if curl -f "http://localhost:${port}/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务已就绪！${NC}"
        break
      fi
      
      echo -n "."
      sleep 2
      ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
      echo -e "${YELLOW}⚠️  服务启动超时，请检查日志: $0 logs docker${NC}"
    fi
  else
    echo -e "${RED}❌ 生产环境部署失败${NC}"
    exit 1
  fi
}

# 更新代码并部署
update_and_deploy() {
  local tag="${1:-latest}"
  local port="${2:-10001}"
  local env_file="${3:-.env.production}"
  
  echo -e "${BLUE}[UPDATE] Updating SpotLight code and deploying...${NC}"
  echo "  Tag: ${tag}"
  echo "  Port: ${port}"
  echo "  Environment: ${env_file}"
  
  # 检查Git仓库状态
  if [[ -d ".git" ]]; then
    echo -e "${BLUE}📥 检查代码更新...${NC}"
    
    # 获取当前分支
    local current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    echo "  Current branch: ${current_branch}"
    
    # 拉取最新代码
    if git pull origin "$current_branch" 2>/dev/null; then
      echo -e "${GREEN}✅ 代码更新成功${NC}"
      
      # 获取最新提交信息
      local latest_commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
      local commit_message=$(git log -1 --pretty=format:"%s" 2>/dev/null || echo "No message")
      echo "  Latest commit: ${latest_commit}"
      echo "  Message: ${commit_message}"
      
      # 更新标签为最新提交
      if [[ "$tag" == "latest" ]]; then
        tag="$latest_commit"
        echo "  Updated tag: ${tag}"
      fi
    else
      echo -e "${YELLOW}⚠️  代码更新失败，继续使用当前版本${NC}"
    fi
  else
    echo -e "${YELLOW}⚠️  未检测到Git仓库，跳过代码更新检查${NC}"
  fi
  
  # 重新构建镜像
  echo -e "${BLUE}🔨 重新构建镜像...${NC}"
  build_image "$tag"
  
  # 部署到生产环境
  echo -e "${BLUE}🚀 部署更新后的服务...${NC}"
  deploy_production "$tag" "$port" "$env_file"
  
  echo -e "${GREEN}✅ 更新部署完成！${NC}"
  echo ""
  echo "💡 更新摘要:"
  echo "  - 镜像标签: ${tag}"
  echo "  - 服务端口: ${port}"
  echo "  - 部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
  echo "🔍 验证部署:"
  echo "  - 健康检查: curl http://localhost:${port}/health"
  echo "  - 服务状态: $0 status"
  echo "  - 查看日志: $0 logs docker"
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

# 创建开发环境Docker Compose文件
create_dev_compose_file() {
  echo -e "${BLUE}🔧 创建开发环境配置文件...${NC}"
  
  cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

services:
  selenium-hub:
    image: selenium/hub:4.15.0
    container_name: spotlight-selenium-hub
    ports:
      - "4442:4442"
      - "4443:4443"
      - "4444:4444"
    environment:
      - GRID_MAX_SESSION=16
      - GRID_BROWSER_TIMEOUT=300
      - GRID_TIMEOUT=300
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4444/wd/hub/status"]
      interval: 30s
      timeout: 10s
      retries: 3

  hybrid-driver-dev:
    build:
      context: .
      dockerfile: Dockerfile.spotlight
    container_name: spotlight-hybrid-driver-dev
    ports:
      - "10001:10001"
    environment:
      - SELENIUM_HUB_URL=http://selenium-hub:4444/wd/hub
      - LOG_LEVEL=debug
      - ENVIRONMENT=development
    volumes:
      - ./hybrid_driver:/app/hybrid_driver
      - ./config:/app/config
    depends_on:
      selenium-hub:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:10001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  chrome-node:
    image: selenium/node-chrome:4.15.0
    container_name: spotlight-chrome-node
    shm_size: 2gb
    depends_on:
      selenium-hub:
        condition: service_healthy
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_NODE_MAX_SESSIONS=4
      - SE_NODE_OVERRIDE_MAX_SESSIONS=true
    restart: unless-stopped

networks:
  default:
    name: spotlight-network
EOF

  echo -e "${GREEN}✅ docker-compose.dev.yml 创建完成${NC}"
}

# 创建SpotLight Dockerfile
create_spotlight_dockerfile() {
  echo -e "${BLUE}🔧 创建Dockerfile...${NC}"
  
  cat > Dockerfile.spotlight << 'EOF'
# SpotLight Hybrid Driver API container managed purely by Poetry
FROM python:3.10-slim AS base

ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    API_HOST=0.0.0.0 \
    API_PORT=10001 \
    PIP_TIMEOUT=300 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    make \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

FROM base AS builder

ENV POETRY_VERSION=2.2.1 \
    POETRY_HOME=/opt/poetry \
    PATH=/opt/poetry/bin:$PATH

RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry config installer.parallel true && \
    poetry install --only main --no-root --no-interaction --no-ansi

FROM base AS runtime

WORKDIR /app

COPY --from=builder /usr/local /usr/local
COPY pyproject.toml poetry.lock ./
COPY hybrid_driver/ ./hybrid_driver/

RUN useradd -m -u 1000 spotlight && \
    mkdir -p logs data cache && \
    chown -R spotlight:spotlight /app

USER spotlight

EXPOSE 10001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10001/health || exit 1

CMD ["python", "hybrid_driver/start_api_server.py", "--host", "0.0.0.0", "--port", "10001"]
EOF

  echo -e "${GREEN}✅ Dockerfile.spotlight 创建完成${NC}"
}

# 创建生产环境配置文件
create_production_env_file() {
  local env_file="$1"
  echo -e "${BLUE}🔧 创建生产环境配置文件...${NC}"
  
  cat > "$env_file" << 'EOF'
# SpotLight API Configuration

# API Host
API_HOST=0.0.0.0

# API Port
API_PORT=10001

# Log Level
LOG_LEVEL=info

# Environment
ENVIRONMENT=production

# Image Tag
IMAGE_TAG=latest

# Docker Registry (if needed for pushing)
# DOCKER_REGISTRY=your_registry.com

# Image Name
IMAGE_NAME=spotlight-api

# Build Arguments
BUILD_DATE=
GIT_COMMIT=
EOF

  echo -e "${GREEN}✅ $env_file 创建完成${NC}"
}

# 创建开发环境配置文件
create_dev_env_file() {
  local env_file="$1"
  echo -e "${BLUE}🔧 创建开发环境配置文件...${NC}"
  
  cat > "$env_file" << 'EOF'
# SpotLight API Development Configuration

# API Host
API_HOST=0.0.0.0

# API Port
API_PORT=10001

# Log Level
LOG_LEVEL=debug

# Environment
ENVIRONMENT=development

# Image Tag
IMAGE_TAG=dev

# Image Name
IMAGE_NAME=spotlight-api

# Build Arguments
BUILD_DATE=
GIT_COMMIT=

# Development Settings
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
EOF

  echo -e "${GREEN}✅ $env_file 创建完成${NC}"
}

# 验证环境配置
validate_environment() {
  local env_file="${1:-.env}"
  
  if [[ -f "$env_file" ]]; then
    echo -e "${BLUE}🔍 验证环境配置: $env_file${NC}"
    
    # 加载环境变量
    set -a
    source "$env_file"
    set +a
    
    # 验证必要的环境变量
    local required_vars=("API_HOST" "API_PORT" "LOG_LEVEL" "ENVIRONMENT")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
      if [[ -z "${!var}" ]]; then
        missing_vars+=("$var")
      fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
      echo -e "${YELLOW}⚠️  缺少必要的环境变量: ${missing_vars[*]}${NC}"
      return 1
    else
      echo -e "${GREEN}✅ 环境配置验证通过${NC}"
      return 0
    fi
  else
    echo -e "${YELLOW}⚠️  环境配置文件不存在: $env_file${NC}"
    return 1
  fi
}

# 清理Docker资源
cleanup_docker() {
  local force="${1:-false}"
  
  echo -e "${BLUE}🧹 清理Docker资源...${NC}"
  
  if [[ "$force" == "true" ]]; then
    echo -e "${YELLOW}⚠️  强制清理模式${NC}"
    
    # 停止并删除所有相关容器
    docker compose -f docker-compose.api.yml down --volumes --remove-orphans 2>/dev/null || true
    docker compose -f docker-compose.dev.yml down --volumes --remove-orphans 2>/dev/null || true
    
    # 删除相关镜像
    docker rmi "$IMAGE_NAME:latest" 2>/dev/null || true
    docker rmi "$IMAGE_NAME:dev" 2>/dev/null || true
    
    # 清理未使用的资源
    docker system prune -f
    
    echo -e "${GREEN}✅ 强制清理完成${NC}"
  else
    echo -e "${BLUE}📋 安全清理模式${NC}"
    
    # 只停止服务，保留数据
    docker compose -f docker-compose.api.yml down 2>/dev/null || true
    docker compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    echo -e "${GREEN}✅ 安全清理完成${NC}"
  fi
}

# 停止本地服务
stop_local_service() {
  echo -e "${BLUE}🛑 停止本地服务...${NC}"
  
  # 查找uvicorn进程
  local pid=$(ps aux | grep "uvicorn.*hybrid_driver.server_optimized:app" | grep -v grep | awk '{print $2}')
  
  if [ -n "$pid" ]; then
    echo -e "${BLUE}🛑 正在停止进程 ${pid}...${NC}"
    kill -TERM "$pid" 2>/dev/null
    
    # 等待进程优雅退出
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
      sleep 1
      count=$((count + 1))
    done
    
    # 如果进程仍然存在，强制杀死
    if kill -0 "$pid" 2>/dev/null; then
      echo -e "${YELLOW}⚠️  进程未响应，强制终止...${NC}"
      kill -KILL "$pid" 2>/dev/null
    fi
    
    sleep 1
    echo -e "${GREEN}✅ 本地服务已停止${NC}"
  else
    echo -e "${YELLOW}⚠️  本地服务未运行，无需停止${NC}"
  fi
}

# 重启本地服务
restart_local_service() {
  echo -e "${BLUE}🔄 重启本地服务...${NC}"
  
  # 先停止服务
  stop_local_service
  
  # 等待一下确保端口释放
  sleep 2
  
  # 重新启动服务
  echo -e "${BLUE}🚀 启动服务...${NC}"
  
  # 获取当前配置
  local host="${HOST:-${API_HOST_DEFAULT:-0.0.0.0}}"
  local port="${PORT:-${API_PORT_DEFAULT:-10001}}"
  
  # 后台启动服务
  nohup "$POETRY_BIN" run uvicorn hybrid_driver.server_optimized:app \
    --host "${host}" \
    --port "${port}" \
    --reload > uvicorn.log 2>&1 &
  
  local new_pid=$!
  sleep 3
  
  # 检查服务是否成功启动
  if kill -0 $new_pid 2>/dev/null; then
    echo -e "${GREEN}✅ 本地服务已重启${NC}"
    echo "🌐 Service: http://${host}:${port}"
    echo "📚 API Docs: http://${host}:${port}/docs"
    echo "💚 Health: http://${host}:${port}/health"
    echo "📝 Logs: tail -f uvicorn.log"
    echo "🛑 Stop: kill $new_pid"
  else
    echo -e "${RED}❌ 本地服务重启失败，请检查日志: uvicorn.log${NC}"
    exit 1
  fi
}

# 显示本地服务状态
show_local_status() {
  echo -e "${BLUE}[STATUS-LOCAL] 本地服务状态:${NC}"
  
  # 查找uvicorn进程
  local pid=$(ps aux | grep "uvicorn.*hybrid_driver.server_optimized:app" | grep -v grep | awk '{print $2}')
  
  if [ -n "$pid" ]; then
    echo -e "  ✅ 本地服务正在运行"
    echo "  📊 进程ID: $pid"
    
    # 检查端口监听状态
    local port="${PORT:-${API_PORT_DEFAULT:-10001}}"
    if netstat -tlnp 2>/dev/null | grep ":$port " >/dev/null; then
      local host_info=$(netstat -tlnp 2>/dev/null | grep ":$port " | head -1)
      echo "  🌐 监听地址: $host_info"
    fi
    
    echo "🌐 Service: http://localhost:$port"
    echo "📚 API Docs: http://localhost:$port/docs"
    echo "💚 Health: http://localhost:$port/health"
    echo "📝 Logs: tail -f uvicorn.log"
    echo "🛑 Stop: ./scripts/spotlight.sh stop"
    echo "🔄 Restart: ./scripts/spotlight.sh restart"
  else
    echo -e "  ❌ 本地服务未运行"
    echo "💡 启动服务: ./scripts/spotlight.sh dev"
  fi
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

🔧 本地服务管理命令:
  stop         - 停止本地服务
  restart      - 重启本地服务
  status-local - 查看本地服务状态

🔧 生产环境管理命令:
  build        - 构建生产镜像
  deploy       - 部署到生产环境
  update       - 更新代码并部署
  status       - 查看部署状态
  logs         - 查看服务日志
  cleanup      - 清理Docker资源

📋 选项:
  --host HOST      指定主机地址
  --port PORT      指定端口号
  --workers N      指定工作进程数 (仅serve模式)
  --log-level LEVEL 指定日志级别
  --tag TAG        指定版本标签 (仅生产命令)
  --force          强制操作 (仅cleanup命令)

🌍 环境变量:
  API_HOST         默认主机地址
  API_PORT         默认端口号
  LOG_LEVEL        默认日志级别
  IMAGE_NAME       镜像名称
  DOCKER_REGISTRY  镜像仓库地址

💡 使用示例:
  # 开发环境
  ./scripts/spotlight.sh dev
  ./scripts/spotlight.sh docker-dev --port 10002
  
  # 生产环境
  ./scripts/spotlight.sh serve --port 10001 --workers 4
  ./scripts/spotlight.sh docker --port 10001
  
  # 生产管理
  ./scripts/spotlight.sh build --tag v1.0.0
  ./scripts/spotlight.sh deploy --tag v1.0.0 --port 10001
  ./scripts/spotlight.sh update --tag v1.0.0 --port 10001
  ./scripts/spotlight.sh status
  ./scripts/spotlight.sh logs docker
  
  # 资源管理
  ./scripts/spotlight.sh cleanup        # 安全清理
  ./scripts/spotlight.sh cleanup --force # 强制清理

📚 更多信息:
  - 快速启动: docs/quick-start.md
  - 详细部署: docs/deployment-guide.md
  - Docker开发: docs/docker-development.md
EOF
}

# 主函数
case "${CMD}" in
  # 服务启动命令
  dev) run_dev;;
  serve|prod|start) run_serve;;
  docker-dev) run_docker_dev;;
  docker) run_docker;;
  
  # 本地服务管理命令
  stop) stop_local_service;;
  restart) restart_local_service;;
  status-local) show_local_status;;
  
  # 生产环境管理命令
  build) 
    tag="${1:-latest}"
    context="${2:-.}"
    build_image "$tag" "$context"
    ;;
  deploy)
    tag="${1:-latest}"
    port="${2:-10001}"
    env_file="${3:-.env.production}"
    deploy_production "$tag" "$port" "$env_file"
    ;;
  update)
    tag="${1:-latest}"
    port="${2:-10001}"
    env_file="${3:-.env.production}"
    update_and_deploy "$tag" "$port" "$env_file"
    ;;
  status) show_status;;
  logs) show_logs "${1:-}";;
  cleanup) 
    force="${1:-false}"
    if [[ "$force" == "--force" ]]; then
      cleanup_docker "true"
    else
      cleanup_docker "false"
    fi
    ;;
  
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


