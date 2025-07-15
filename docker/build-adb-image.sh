#!/bin/bash

# 构建带 ADB 功能的自定义 Selenium Chrome 镜像脚本

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

# 检查必要文件
check_files() {
    local required_files=(
        "Dockerfile.custom-selenium-chrome"
        "docker-compose.custom-selenium-adb.yml"
        "scripts/custom_startup.sh"
        "scripts/adb_init.sh"
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
    print_message $BLUE "开始构建带 ADB 功能的自定义 Selenium Chrome 镜像..."
    
    # 创建必要的目录
    mkdir -p logs adb_config
    
    # 构建镜像
    docker compose -f docker-compose.custom-selenium-adb.yml build --no-cache
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✓ 镜像构建成功"
    else
        print_message $RED "✗ 镜像构建失败"
        exit 1
    fi
}

# 测试镜像
test_image() {
    print_message $BLUE "测试带 ADB 功能的镜像..."
    
    # 停止可能存在的容器
    docker compose -f docker-compose.custom-selenium-adb.yml down 2>/dev/null || true
    
    # 启动容器
    docker compose -f docker-compose.custom-selenium-adb.yml up -d custom-selenium-chrome-adb
    
    # 等待容器启动
    print_message $YELLOW "等待容器启动..."
    sleep 15
    
    # 检查容器状态
    if docker compose -f docker-compose.custom-selenium-adb.yml ps | grep -q "Up"; then
        print_message $GREEN "✓ 容器启动成功"
    else
        print_message $RED "✗ 容器启动失败"
        docker compose -f docker-compose.custom-selenium-adb.yml logs custom-selenium-chrome-adb
        exit 1
    fi
    
    # 检查 ADB 功能
    print_message $BLUE "检查 ADB 功能..."
    local container_id=$(docker compose -f docker-compose.custom-selenium-adb.yml ps -q custom-selenium-chrome-adb)
    
    # 检查 ADB 是否安装
    if docker exec "$container_id" which adb; then
        print_message $GREEN "✓ ADB 已安装"
    else
        print_message $RED "✗ ADB 未安装"
    fi
    
    # 检查 ADB 服务器状态
    if docker exec "$container_id" adb devices; then
        print_message $GREEN "✓ ADB 服务器运行正常"
    else
        print_message $RED "✗ ADB 服务器异常"
    fi
    
    # 显示容器信息
    print_message $BLUE "容器信息:"
    docker compose -f docker-compose.custom-selenium-adb.yml ps
    
    print_message $BLUE "容器日志 (最近 20 行):"
    docker compose -f docker-compose.custom-selenium-adb.yml logs --tail=20 custom-selenium-chrome-adb
}

# 显示使用说明
show_usage() {
    print_message $BLUE "带 ADB 功能的自定义 Selenium Chrome 镜像构建脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  build     构建镜像"
    echo "  test      构建并测试镜像"
    echo "  start     启动测试容器"
    echo "  stop      停止测试容器"
    echo "  logs      查看容器日志"
    echo "  adb       进入容器执行 ADB 命令"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 build    # 仅构建镜像"
    echo "  $0 test     # 构建并测试镜像"
    echo "  $0 adb      # 进入容器执行 ADB 命令"
}

# 进入容器执行 ADB 命令
exec_adb() {
    local container_id=$(docker compose -f docker-compose.custom-selenium-adb.yml ps -q custom-selenium-chrome-adb)
    if [ -n "$container_id" ]; then
        print_message $BLUE "进入容器执行 ADB 命令..."
        docker exec -it "$container_id" bash
    else
        print_message $RED "容器未运行，请先启动容器"
    fi
}

# 主函数
main() {
    case "${1:-help}" in
        build)
            check_files
            build_image
            ;;
        test)
            check_files
            build_image
            test_image
            print_message $GREEN "✓ 测试完成！"
            print_message $YELLOW "提示: 使用 '$0 stop' 停止测试容器"
            ;;
        start)
            docker compose -f docker-compose.custom-selenium-adb.yml up -d custom-selenium-chrome-adb
            print_message $GREEN "✓ 容器已启动"
            ;;
        stop)
            docker compose -f docker-compose.custom-selenium-adb.yml down
            print_message $GREEN "✓ 容器已停止"
            ;;
        logs)
            docker compose -f docker-compose.custom-selenium-adb.yml logs -f custom-selenium-chrome-adb
            ;;
        adb)
            exec_adb
            ;;
        help|*)
            show_usage
            ;;
    esac
}

# 脚本入口
main "$@" 