#!/bin/bash

# 自定义 Selenium Chrome 镜像构建和测试脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查 Docker 是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_message $RED "错误: Docker 未运行或无法访问"
        exit 1
    fi
    print_message $GREEN "✓ Docker 运行正常"
}

# 检查必要文件
check_files() {
    local required_files=(
        "Dockerfile.custom-selenium-chrome"
        "docker-compose.custom-selenium.yml"
        "scripts/custom_startup.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_message $RED "错误: 缺少必要文件: $file"
            exit 1
        fi
    done
    print_message $GREEN "✓ 所有必要文件存在"
}

# 构建镜像
build_image() {
    print_message $BLUE "开始构建自定义 Selenium Chrome 镜像..."
    
    docker compose -f docker-compose.custom-selenium.yml build --no-cache
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✓ 镜像构建成功"
    else
        print_message $RED "✗ 镜像构建失败"
        exit 1
    fi
}

# 启动测试容器
start_test_container() {
    print_message $BLUE "启动测试容器..."
    
    # 停止可能存在的容器
    docker compose -f docker-compose.custom-selenium.yml down 2>/dev/null || true
    
    # 启动生产模式容器
    docker compose -f docker-compose.custom-selenium.yml up -d custom-selenium-chrome
    
    # 等待容器启动
    print_message $YELLOW "等待容器启动..."
    sleep 10
    
    # 检查容器状态
    if docker compose -f docker-compose.custom-selenium.yml ps | grep -q "Up"; then
        print_message $GREEN "✓ 测试容器启动成功"
    else
        print_message $RED "✗ 测试容器启动失败"
        docker compose -f docker-compose.custom-selenium.yml logs custom-selenium-chrome
        exit 1
    fi
}

# 测试 Selenium 服务
test_selenium_service() {
    print_message $BLUE "测试 Selenium 服务..."
    
    # 等待服务完全启动
    sleep 5
    
    # 测试 WebDriver 端点
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4444/status)
    
    if [ "$response" = "200" ]; then
        print_message $GREEN "✓ Selenium WebDriver 服务正常"
    else
        print_message $RED "✗ Selenium WebDriver 服务异常 (HTTP: $response)"
        return 1
    fi
    
    # 测试自定义脚本日志
    local container_id=$(docker compose -f docker-compose.custom-selenium.yml ps -q custom-selenium-chrome)
    if docker exec "$container_id" test -f /opt/scripts/logs/startup.log; then
        print_message $GREEN "✓ 自定义启动脚本日志文件存在"
    else
        print_message $YELLOW "⚠ 自定义启动脚本日志文件不存在"
    fi
}

# 显示容器信息
show_container_info() {
    print_message $BLUE "容器信息:"
    echo "----------------------------------------"
    docker compose -f docker-compose.custom-selenium.yml ps
    echo ""
    
    print_message $BLUE "容器日志 (最近 20 行):"
    echo "----------------------------------------"
    docker compose -f docker-compose.custom-selenium.yml logs --tail=20 custom-selenium-chrome
    echo ""
    
    print_message $BLUE "自定义启动脚本日志:"
    echo "----------------------------------------"
    local container_id=$(docker compose -f docker-compose.custom-selenium.yml ps -q custom-selenium-chrome)
    if [ -n "$container_id" ]; then
        docker exec "$container_id" cat /opt/scripts/logs/startup.log 2>/dev/null || echo "日志文件不存在"
    fi
    echo ""
}

# 清理测试环境
cleanup() {
    print_message $YELLOW "清理测试环境..."
    docker compose -f docker-compose.custom-selenium.yml down
    print_message $GREEN "✓ 清理完成"
}

# 显示使用说明
show_usage() {
    print_message $BLUE "自定义 Selenium Chrome 镜像构建和测试脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  build     构建镜像"
    echo "  test      构建并测试镜像"
    echo "  start     启动测试容器"
    echo "  stop      停止测试容器"
    echo "  logs      查看容器日志"
    echo "  info      显示容器信息"
    echo "  cleanup   清理测试环境"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 build    # 仅构建镜像"
    echo "  $0 test     # 构建并测试镜像"
    echo "  $0 logs     # 查看日志"
}

# 主函数
main() {
    case "${1:-help}" in
        build)
            check_docker
            check_files
            build_image
            ;;
        test)
            check_docker
            check_files
            build_image
            start_test_container
            test_selenium_service
            show_container_info
            print_message $GREEN "✓ 测试完成！"
            print_message $YELLOW "提示: 使用 '$0 stop' 停止测试容器"
            ;;
        start)
            check_docker
            start_test_container
            show_container_info
            ;;
        stop)
            docker compose -f docker-compose.custom-selenium.yml down
            print_message $GREEN "✓ 容器已停止"
            ;;
        logs)
            docker compose -f docker-compose.custom-selenium.yml logs -f custom-selenium-chrome
            ;;
        info)
            show_container_info
            ;;
        cleanup)
            cleanup
            ;;
        help|*)
            show_usage
            ;;
    esac
}

# 脚本入口
main "$@" 