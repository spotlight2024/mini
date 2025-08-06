#!/bin/bash

# Docker代理测试脚本
# 用于测试Docker容器中的代理功能

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

print_message $BLUE "=== Docker代理测试脚本 ==="

# 检查Docker是否运行
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
        "docker-compose.custom-selenium-adb.yml"
        "proxy.env"
        "scripts/custom_startup.sh"
        "scripts/setup_proxy_config.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_message $RED "错误: 缺少必要文件: $file"
            exit 1
        fi
    done
    print_message $GREEN "✓ 所有必要文件存在"
}

# 构建测试镜像
build_test_image() {
    print_message $BLUE "构建测试镜像..."
    
    # 清理旧镜像
    docker rmi custom-selenium-chrome:test 2>/dev/null || true
    
    # 构建新镜像
    docker build -f Dockerfile.custom-selenium-chrome -t custom-selenium-chrome:test .
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ 测试镜像构建成功"
    else
        print_message $RED "❌ 测试镜像构建失败"
        exit 1
    fi
}

# 启动测试容器
start_test_container() {
    print_message $BLUE "启动测试容器..."
    
    # 停止可能存在的容器
    docker stop test-proxy-container 2>/dev/null || true
    docker rm test-proxy-container 2>/dev/null || true
    
    # 启动测试容器
    docker run -d \
        --name test-proxy-container \
        --env-file proxy.env \
        --env PROXY_ENABLED=true \
        --env ADB_PROXY_LOG_LEVEL=DEBUG \
        custom-selenium-chrome:test \
        sleep infinity
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ 测试容器启动成功"
        
        # 等待容器启动
        sleep 3
        
        # 检查容器状态
        if docker ps | grep -q test-proxy-container; then
            print_message $GREEN "✅ 容器运行正常"
        else
            print_message $RED "❌ 容器启动失败"
            docker logs test-proxy-container
            exit 1
        fi
    else
        print_message $RED "❌ 测试容器启动失败"
        exit 1
    fi
}

# 测试代理配置
test_proxy_config() {
    print_message $BLUE "测试代理配置..."
    
    # 测试代理配置脚本
    docker exec test-proxy-container /opt/custom-scripts/setup_proxy_config.sh
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ 代理配置脚本执行成功"
        
        # 检查扩展文件是否生成
        if docker exec test-proxy-container test -f /opt/chrome_extensions/proxy_auth/manifest.json; then
            print_message $GREEN "✅ Chrome扩展文件生成成功"
        else
            print_message $RED "❌ Chrome扩展文件生成失败"
        fi
        
        if docker exec test-proxy-container test -f /opt/chrome_extensions/proxy_auth/background.js; then
            print_message $GREEN "✅ Chrome扩展脚本生成成功"
        else
            print_message $RED "❌ Chrome扩展脚本生成失败"
        fi
    else
        print_message $RED "❌ 代理配置脚本执行失败"
    fi
}

# 测试ADB代理
test_adb_proxy() {
    print_message $BLUE "测试ADB代理..."
    
    # 启动ADB代理服务
    docker exec test-proxy-container /opt/custom-scripts/custom_startup.sh
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ ADB代理服务启动成功"
        
        # 等待服务启动
        sleep 5
        
        # 检查ADB代理进程
        if docker exec test-proxy-container ps aux | grep -q adb_proxy; then
            print_message $GREEN "✅ ADB代理进程运行正常"
        else
            print_message $RED "❌ ADB代理进程未运行"
        fi
        
        # 检查端口监听
        if docker exec test-proxy-container netstat -tlnp | grep -q ":5037"; then
            print_message $GREEN "✅ ADB代理端口监听正常"
        else
            print_message $RED "❌ ADB代理端口监听失败"
        fi
    else
        print_message $RED "❌ ADB代理服务启动失败"
    fi
}

# 测试Chrome包装脚本
test_chrome_wrapper() {
    print_message $BLUE "测试Chrome包装脚本..."
    
    # 检查Chrome包装脚本
    if docker exec test-proxy-container test -f /usr/local/bin/chrome-with-proxy; then
        print_message $GREEN "✅ Chrome包装脚本存在"
    else
        print_message $RED "❌ Chrome包装脚本不存在"
    fi
    
    # 检查Chrome符号链接
    if docker exec test-proxy-container test -L /usr/bin/google-chrome; then
        print_message $GREEN "✅ Chrome符号链接已创建"
    else
        print_message $RED "❌ Chrome符号链接未创建"
    fi
    
    # 检查原始Chrome备份
    if docker exec test-proxy-container test -f /usr/bin/google-chrome.original; then
        print_message $GREEN "✅ 原始Chrome备份存在"
    else
        print_message $RED "❌ 原始Chrome备份不存在"
    fi
}

# 显示容器信息
show_container_info() {
    print_message $BLUE "容器信息:"
    echo "----------------------------------------"
    docker ps | grep test-proxy-container
    echo ""
    
    print_message $BLUE "容器日志 (最近 20 行):"
    echo "----------------------------------------"
    docker logs --tail=20 test-proxy-container
    echo ""
    
    print_message $BLUE "扩展目录内容:"
    echo "----------------------------------------"
    docker exec test-proxy-container ls -la /opt/chrome_extensions/proxy_auth/ 2>/dev/null || echo "扩展目录不存在"
    echo ""
    
    print_message $BLUE "ADB代理进程:"
    echo "----------------------------------------"
    docker exec test-proxy-container ps aux | grep adb_proxy || echo "ADB代理进程未运行"
    echo ""
}

# 清理测试环境
cleanup() {
    print_message $YELLOW "清理测试环境..."
    docker stop test-proxy-container 2>/dev/null || true
    docker rm test-proxy-container 2>/dev/null || true
    docker rmi custom-selenium-chrome:test 2>/dev/null || true
    print_message $GREEN "✅ 清理完成"
}

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --build-only        仅构建镜像，不运行测试"
    echo "  --test-only         仅运行测试，不构建镜像"
    echo "  --clean             清理测试环境"
    echo "  --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                  构建镜像并运行完整测试"
    echo "  $0 --build-only     仅构建镜像"
    echo "  $0 --test-only      仅运行测试"
    echo "  $0 --clean          清理测试环境"
}

# 主函数
main() {
    local build_only=false
    local test_only=false
    local cleanup_flag=false
    
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
            --clean)
                cleanup_flag=true
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
    
    # 检查Docker
    check_docker
    
    # 检查文件
    check_files
    
    if [ "$cleanup_flag" = true ]; then
        print_message $BLUE "清理模式..."
        cleanup
    elif [ "$test_only" = true ]; then
        print_message $BLUE "仅测试模式..."
        start_test_container
        test_proxy_config
        test_adb_proxy
        test_chrome_wrapper
        show_container_info
        print_message $GREEN "✅ 测试完成！"
    elif [ "$build_only" = true ]; then
        print_message $BLUE "仅构建模式..."
        build_test_image
    else
        # 默认模式：构建并测试
        print_message $BLUE "执行完整测试流程..."
        build_test_image
        start_test_container
        test_proxy_config
        test_adb_proxy
        test_chrome_wrapper
        show_container_info
        print_message $GREEN "✅ 完整测试完成！"
        print_message $YELLOW "提示: 使用 '$0 --clean' 清理测试环境"
    fi
}

# 执行主函数
main "$@"
