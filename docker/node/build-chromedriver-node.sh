#!/bin/bash

# ChromeDriver Node 构建和部署脚本
# 使用方法: ./build-chromedriver-node.sh [build|start|stop|test|logs|clean]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PROJECT_NAME="mini"
SERVICE_NAME="chromedriver-node"
IMAGE_NAME="${PROJECT_NAME}_${SERVICE_NAME}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查必要文件
check_files() {
    log "检查必要文件..."
    
    local files=(
        "Dockerfile.chromedriver-node"
        "chromedriver-node.toml"
        "chromedriver-entrypoint.sh"
        "docker-compose.yml"
    )
    
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            error "缺少必要文件: $file"
            exit 1
        fi
    done
    
    success "所有必要文件检查通过"
}

# 构建镜像
build_image() {
    log "构建 ChromeDriver 节点镜像..."
    
    # 设置构建参数
    CHROMEDRIVER_VERSION=${CHROMEDRIVER_VERSION:-"128.0.6613.0"}
    
    docker build \
        --build-arg CHROMEDRIVER_VERSION="$CHROMEDRIVER_VERSION" \
        --tag "$IMAGE_NAME:latest" \
        --tag "$IMAGE_NAME:$(date +%Y%m%d-%H%M%S)" \
        --file Dockerfile.chromedriver-node \
        . || {
        error "镜像构建失败"
        exit 1
    }
    
    success "镜像构建完成: $IMAGE_NAME"
}

# 启动服务
start_services() {
    log "启动 ChromeDriver 节点服务..."
    
    # 先启动 Hub
    docker-compose up -d selenium-hub
    
    # 等待 Hub 就绪
    log "等待 Selenium Hub 启动..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -sSf http://localhost:4444/status >/dev/null 2>&1; then
            success "Selenium Hub 已就绪"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        warning "Selenium Hub 启动超时，但继续启动节点"
    fi
    
    # 启动 ChromeDriver 节点
    docker-compose up -d "$SERVICE_NAME"
    
    # 等待节点注册
    log "等待节点注册到 Grid..."
    sleep 10
    
    # 检查节点状态
    if check_node_status; then
        success "ChromeDriver 节点启动成功"
        show_service_info
    else
        error "ChromeDriver 节点启动失败"
        docker-compose logs "$SERVICE_NAME"
        exit 1
    fi
}

# 检查节点状态
check_node_status() {
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "检查节点状态 (尝试 $attempt/$max_attempts)..."
        
        if curl -sSf http://localhost:4444/status >/dev/null 2>&1; then
            local node_count=$(curl -s http://localhost:4444/status | jq -r '.value.nodes | length' 2>/dev/null || echo "0")
            if [ "$node_count" -gt 0 ]; then
                success "发现 $node_count 个注册节点"
                return 0
            fi
        fi
        
        sleep 5
        attempt=$((attempt + 1))
    done
    
    return 1
}

# 显示服务信息
show_service_info() {
    log "服务信息:"
    echo "----------------------------------------"
    echo "🌐 Selenium Grid Console: http://localhost:4444"
    echo "🌐 Grid Status API: http://localhost:4444/status"
    echo "🌐 Grid WebDriver Hub: http://localhost:4444/wd/hub"
    echo "📱 支持功能: Android WebView + 远程 Chrome 实例"
    echo "🐳 Container Status:"
    docker-compose ps selenium-hub "$SERVICE_NAME"
    echo "----------------------------------------"
}

# 停止服务
stop_services() {
    log "停止 ChromeDriver 节点服务..."
    docker-compose stop "$SERVICE_NAME" selenium-hub
    success "服务已停止"
}

# 运行测试
run_tests() {
    log "运行 ChromeDriver 节点功能测试..."
    
    # 检查 Python 环境
    if ! command -v python3 &> /dev/null; then
        error "Python3 未安装"
        exit 1
    fi
    
    # 安装依赖
    if [ ! -f "chromedriver-test.py" ]; then
        error "测试脚本不存在: chromedriver-test.py"
        exit 1
    fi
    
    log "安装 Python 依赖..."
    pip install selenium requests || {
        warning "依赖安装失败，请手动安装: pip install selenium requests"
    }
    
    # 运行测试
    log "执行功能测试..."
    python3 chromedriver-test.py
}

# 查看日志
show_logs() {
    local service=${1:-"$SERVICE_NAME"}
    log "查看 $service 服务日志..."
    docker-compose logs -f "$service"
}

# 清理资源
clean_up() {
    log "清理 Docker 资源..."
    
    # 停止服务
    docker-compose down
    
    # 删除镜像
    read -p "是否删除构建的镜像? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker rmi "$IMAGE_NAME" 2>/dev/null || true
        success "镜像已删除"
    fi
    
    # 清理未使用的 Docker 资源
    read -p "是否清理未使用的 Docker 资源? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -f
        success "Docker 资源清理完成"
    fi
}

# 显示帮助信息
show_help() {
    echo "ChromeDriver Node 管理脚本"
    echo ""
    echo "使用方法: $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  build   - 构建 ChromeDriver 节点镜像"
    echo "  start   - 启动服务 (Hub + ChromeDriver Node)"
    echo "  stop    - 停止服务"
    echo "  test    - 运行功能测试"
    echo "  logs    - 查看服务日志"
    echo "  status  - 检查服务状态"
    echo "  clean   - 清理 Docker 资源"
    echo "  help    - 显示此帮助信息"
    echo ""
    echo "环境变量:"
    echo "  CHROMEDRIVER_VERSION - ChromeDriver 版本 (默认: 128.0.6613.0)"
    echo ""
    echo "示例:"
    echo "  $0 build    # 构建镜像"
    echo "  $0 start    # 启动服务"
    echo "  $0 test     # 运行测试"
    echo "  $0 logs     # 查看日志"
}

# 主逻辑
main() {
    case "${1:-help}" in
        "build")
            check_files
            build_image
            ;;
        "start")
            check_files
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "test")
            run_tests
            ;;
        "logs")
            show_logs "${2:-$SERVICE_NAME}"
            ;;
        "status")
            show_service_info
            check_node_status && success "节点状态正常" || error "节点状态异常"
            ;;
        "clean")
            clean_up
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@" 