#!/bin/bash

# 构建和测试Chrome代理扩展的完整流程

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message $BLUE "=== Chrome代理扩展构建和测试流程 ==="

# 检查必要文件
check_files() {
    print_message $YELLOW "检查必要文件..."
    
    required_files=(
        "Dockerfile.custom-selenium-chrome"
        "docker-compose.yml"
        "scripts/setup_proxy_config.sh"
        "scripts/custom_startup.sh"
        "test_in_container.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_message $RED "错误: 缺少必要文件: $file"
            exit 1
        fi
    done
    
    print_message $GREEN "✓ 所有必要文件存在"
}

# 构建Docker镜像
build_image() {
    print_message $BLUE "开始构建Docker镜像..."
    
    # 清理旧镜像
    print_message $YELLOW "清理旧镜像..."
    docker rmi custom-selenium-chrome:adb_proxy 2>/dev/null || true
    
    # 构建新镜像
    print_message $BLUE "构建新镜像..."
    docker build -f Dockerfile.custom-selenium-chrome -t custom-selenium-chrome:adb_proxy .
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ 镜像构建成功: custom-selenium-chrome:adb_proxy"
    else
        print_message $RED "❌ 镜像构建失败"
        exit 1
    fi
}

# 启动测试容器
start_test_container() {
    print_message $BLUE "启动测试容器..."
    
    # 停止并删除旧容器
    docker stop test-proxy-container 2>/dev/null || true
    docker rm test-proxy-container 2>/dev/null || true
    
    # 启动新容器
    docker run -d \
        --name test-proxy-container \
        --env PROXY_HOST=61.132.231.167 \
        --env PROXY_PORT=57001 \
        --env PROXY_USERNAME=vgmpgv \
        --env PROXY_PASSWORD=1bk79g9y \
        --env PROXY_ENABLED=true \
        custom-selenium-chrome:adb_proxy \
        sleep infinity
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ 测试容器启动成功"
    else
        print_message $RED "❌ 测试容器启动失败"
        exit 1
    fi
}

# 在容器中运行测试
run_container_tests() {
    print_message $BLUE "在容器中运行测试..."
    
    # 等待容器完全启动
    sleep 5
    
    # 运行测试脚本
    docker exec test-proxy-container /opt/custom-scripts/test_in_container.sh
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ 容器内测试成功"
    else
        print_message $RED "❌ 容器内测试失败"
        exit 1
    fi
}

# 测试Docker Compose集成
test_docker_compose() {
    print_message $BLUE "测试Docker Compose集成..."
    
    # 停止测试容器
    docker stop test-proxy-container 2>/dev/null || true
    docker rm test-proxy-container 2>/dev/null || true
    
    # 使用Docker Compose启动服务
    print_message $YELLOW "使用Docker Compose启动服务..."
    docker compose --env-file proxy.env up -d
    
    # 等待服务启动
    sleep 10
    
    # 检查服务状态
    if docker compose ps | grep -q "Up"; then
        print_message $GREEN "✅ Docker Compose服务启动成功"
        
        # 检查Chrome容器中的扩展
        print_message $YELLOW "检查Chrome扩展..."
        docker compose exec chrome-driver ls -la /opt/chrome_extensions/proxy_auth/ || true
        
        # 检查代理配置
        print_message $YELLOW "检查代理配置..."
        docker compose exec chrome-driver cat /opt/chrome_extensions/proxy_auth/proxy_config.json || true
        
    else
        print_message $RED "❌ Docker Compose服务启动失败"
        docker compose logs
        exit 1
    fi
}

# 清理资源
cleanup() {
    print_message $YELLOW "清理资源..."
    
    # 停止并删除测试容器
    docker stop test-proxy-container 2>/dev/null || true
    docker rm test-proxy-container 2>/dev/null || true
    
    # 停止Docker Compose服务
    docker compose down 2>/dev/null || true
    
    print_message $GREEN "✓ 资源清理完成"
}

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --build-only        仅构建镜像，不运行测试"
    echo "  --test-only         仅运行测试，不构建镜像"
    echo "  --compose-test      测试Docker Compose集成"
    echo "  --cleanup           清理所有资源"
    echo "  --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                  完整构建和测试流程"
    echo "  $0 --build-only     仅构建镜像"
    echo "  $0 --test-only      仅运行测试"
    echo "  $0 --compose-test   测试Docker Compose"
}

# 主函数
main() {
    local build_only=false
    local test_only=false
    local compose_test=false
    local cleanup_only=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build-only)
                build_only=true
                shift
                ;;
            --test-only)
                test_only=true
                shift
                ;;
            --compose-test)
                compose_test=true
                shift
                ;;
            --cleanup)
                cleanup_only=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                echo "错误: 未知参数 $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # 设置清理陷阱
    trap cleanup EXIT
    
    if [ "$cleanup_only" = true ]; then
        cleanup
        exit 0
    fi
    
    # 检查文件
    check_files
    
    if [ "$test_only" = true ]; then
        print_message $BLUE "仅运行测试模式..."
        run_container_tests
    elif [ "$build_only" = true ]; then
        print_message $BLUE "仅构建模式..."
        build_image
    elif [ "$compose_test" = true ]; then
        print_message $BLUE "Docker Compose测试模式..."
        test_docker_compose
    else
        # 完整流程
        print_message $BLUE "执行完整构建和测试流程..."
        
        # 构建镜像
        build_image
        
        # 启动测试容器
        start_test_container
        
        # 运行测试
        run_container_tests
        
        # 测试Docker Compose集成
        test_docker_compose
        
        print_message $GREEN "=== 所有测试完成 ==="
        print_message $GREEN "✅ Chrome代理扩展构建和测试成功"
    fi
}

# 执行主函数
main "$@"
