#!/bin/bash

# Chrome代理扩展构建脚本

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

print_message $BLUE "=== Chrome代理扩展构建脚本 ==="

# 检查必要文件
check_files() {
    print_message $YELLOW "检查必要文件..."
    
    required_files=(
        "Dockerfile.custom-selenium-chrome"
        "docker-compose.yml"
        "scripts/setup_proxy_config.sh"
        "scripts/custom_startup.sh"
        "test.sh"
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

# 测试镜像
test_image() {
    print_message $BLUE "测试镜像功能..."
    
    # 启动测试容器
    print_message $YELLOW "启动测试容器..."
    docker stop test-proxy-container 2>/dev/null || true
    docker rm test-proxy-container 2>/dev/null || true
    
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
        
        # 等待容器启动
        sleep 3
        
        # 运行测试
        print_message $BLUE "运行容器内测试..."
        docker exec test-proxy-container /opt/custom-scripts/test.sh
        
        if [ $? -eq 0 ]; then
            print_message $GREEN "✅ 镜像测试成功"
        else
            print_message $RED "❌ 镜像测试失败"
        fi
        
        # 清理测试容器
        docker stop test-proxy-container
        docker rm test-proxy-container
    else
        print_message $RED "❌ 测试容器启动失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    print_message $BLUE "启动Docker Compose服务..."
    
    # 停止现有服务
    docker compose down 2>/dev/null || true
    
    # 启动服务
    docker compose --env-file proxy.env up -d
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ 服务启动成功"
        print_message $YELLOW "查看服务状态: docker compose ps"
        print_message $YELLOW "查看日志: docker compose logs -f"
    else
        print_message $RED "❌ 服务启动失败"
        exit 1
    fi
}

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --build-only        仅构建镜像，不运行测试"
    echo "  --test-only         仅运行测试，不构建镜像"
    echo "  --start             构建镜像并启动服务"
    echo "  --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                  构建镜像并运行测试"
    echo "  $0 --build-only     仅构建镜像"
    echo "  $0 --test-only      仅运行测试"
    echo "  $0 --start          构建镜像并启动服务"
}

# 主函数
main() {
    local build_only=false
    local test_only=false
    local start_services_flag=false
    
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
            --start)
                start_services_flag=true
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
    
    # 检查文件
    check_files
    
    if [ "$test_only" = true ]; then
        print_message $BLUE "仅运行测试模式..."
        test_image
    elif [ "$build_only" = true ]; then
        print_message $BLUE "仅构建模式..."
        build_image
    elif [ "$start_services_flag" = true ]; then
        print_message $BLUE "构建并启动服务模式..."
        build_image
        start_services
    else
        # 默认模式：构建并测试
        print_message $BLUE "执行构建和测试流程..."
        build_image
        test_image
        print_message $GREEN "=== 构建和测试完成 ==="
    fi
}

# 执行主函数
main "$@"
