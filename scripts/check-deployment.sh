#!/bin/bash

# SpotLight 部署状态检查脚本
# 用于验证本地部署和Docker部署的状态

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="10001"
HEALTH_ENDPOINT="/health"
DOCS_ENDPOINT="/docs"

# 打印带颜色的消息
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✓ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}✗ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ $message${NC}"
            ;;
    esac
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local host=$2
    
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i:$port >/dev/null 2>&1; then
            return 0
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -an | grep ":$port " | grep LISTEN >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# 检查HTTP端点
check_http_endpoint() {
    local url=$1
    local description=$2
    
    if command -v curl >/dev/null 2>&1; then
        if curl -s -f "$url" >/dev/null 2>&1; then
            print_status "SUCCESS" "$description 可访问: $url"
            return 0
        else
            print_status "ERROR" "$description 不可访问: $url"
            return 1
        fi
    else
        print_status "WARNING" "未安装curl，无法检查HTTP端点"
        return 1
    fi
}

# 检查本地部署
check_local_deployment() {
    print_status "INFO" "检查本地部署状态..."
    
    local host=${LOCAL_HOST:-$DEFAULT_HOST}
    local port=${LOCAL_PORT:-$DEFAULT_PORT}
    
    # 检查端口占用
    if check_port $port $host; then
        print_status "SUCCESS" "端口 $port 已被占用"
        
        # 检查健康端点
        local health_url="http://$host:$port$HEALTH_ENDPOINT"
        if check_http_endpoint "$health_url" "健康检查端点"; then
            print_status "SUCCESS" "本地服务运行正常"
            return 0
        fi
    else
        print_status "WARNING" "端口 $port 未被占用，本地服务可能未启动"
    fi
    
    return 1
}

# 检查Docker部署
check_docker_deployment() {
    print_status "INFO" "检查Docker部署状态..."
    
    if ! command -v docker >/dev/null 2>&1; then
        print_status "ERROR" "Docker未安装或不在PATH中"
        return 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_status "ERROR" "Docker服务未运行"
        return 1
    fi
    
    # 检查spotlight-api容器
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "spotlight-api"; then
        print_status "SUCCESS" "spotlight-api 容器正在运行"
        
        # 检查容器健康状态
        local container_id=$(docker ps -q --filter "name=spotlight-api")
        if [ -n "$container_id" ]; then
            local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_id" 2>/dev/null || echo "unknown")
            if [ "$health_status" = "healthy" ]; then
                print_status "SUCCESS" "容器健康检查通过"
            elif [ "$health_status" = "unhealthy" ]; then
                print_status "ERROR" "容器健康检查失败"
            else
                print_status "WARNING" "容器健康状态: $health_status"
            fi
        fi
        
        return 0
    else
        print_status "WARNING" "spotlight-api 容器未运行"
        return 1
    fi
}

# 检查Docker Compose状态
check_docker_compose() {
    if [ -f "docker-compose.api.yml" ]; then
        print_status "INFO" "检查Docker Compose状态..."
        
        if docker compose -f docker-compose.api.yml ps | grep -q "spotlight-api"; then
            print_status "SUCCESS" "Docker Compose服务正在运行"
            docker compose -f docker-compose.api.yml ps
            return 0
        else
            print_status "WARNING" "Docker Compose服务未运行"
            return 1
        fi
    else
        print_status "WARNING" "未找到docker-compose.api.yml文件"
        return 1
    fi
}

# 检查系统资源
check_system_resources() {
    print_status "INFO" "检查系统资源..."
    
    # 检查内存
    if command -v free >/dev/null 2>&1; then
        local total_mem=$(free -m | awk 'NR==2{print $2}')
        local available_mem=$(free -m | awk 'NR==2{print $7}')
        print_status "INFO" "内存: ${available_mem}MB 可用 / ${total_mem}MB 总计"
        
        if [ $available_mem -lt 1024 ]; then
            print_status "WARNING" "可用内存不足1GB，可能影响服务性能"
        fi
    fi
    
    # 检查磁盘空间
    if command -v df >/dev/null 2>&1; then
        local disk_usage=$(df -h . | awk 'NR==2{print $5}' | sed 's/%//')
        print_status "INFO" "当前目录磁盘使用率: ${disk_usage}%"
        
        if [ $disk_usage -gt 90 ]; then
            print_status "WARNING" "磁盘空间不足，使用率超过90%"
        fi
    fi
}

# 显示帮助信息
show_help() {
    echo "SpotLight 部署状态检查脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示此帮助信息"
    echo "  -l, --local             仅检查本地部署"
    echo "  -d, --docker            仅检查Docker部署"
    echo "  -a, --all               检查所有部署方式（默认）"
    echo "  --host HOST             指定主机地址（默认: 127.0.0.1）"
    echo "  --port PORT             指定端口号（默认: 10001）"
    echo ""
    echo "环境变量:"
    echo "  LOCAL_HOST              本地部署主机地址"
    echo "  LOCAL_PORT              本地部署端口号"
    echo ""
    echo "示例:"
    echo "  $0                      # 检查所有部署"
    echo "  $0 --local              # 仅检查本地部署"
    echo "  $0 --docker             # 仅检查Docker部署"
    echo "  $0 --port 8080          # 检查端口8080的部署"
}

# 主函数
main() {
    local check_local=true
    local check_docker=true
    local host=$DEFAULT_HOST
    local port=$DEFAULT_PORT
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -l|--local)
                check_docker=false
                shift
                ;;
            -d|--docker)
                check_local=false
                shift
                ;;
            -a|--all)
                check_local=true
                check_docker=true
                shift
                ;;
            --host)
                host="$2"
                shift 2
                ;;
            --port)
                port="$2"
                shift 2
                ;;
            *)
                echo "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo "🔍 SpotLight 部署状态检查"
    echo "================================"
    echo "检查时间: $(date)"
    echo "目标地址: $host:$port"
    echo ""
    
    # 检查系统资源
    check_system_resources
    echo ""
    
    # 检查本地部署
    if [ "$check_local" = true ]; then
        if check_local_deployment; then
            local_healthy=true
        else
            local_healthy=false
        fi
        echo ""
    fi
    
    # 检查Docker部署
    if [ "$check_docker" = true ]; then
        if check_docker_deployment; then
            docker_healthy=true
        else
            docker_healthy=false
        fi
        echo ""
        
        check_docker_compose
        echo ""
    fi
    
    # 总结
    echo "📊 部署状态总结"
    echo "================================"
    
    if [ "$check_local" = true ]; then
        if [ "$local_healthy" = true ]; then
            print_status "SUCCESS" "本地部署: 正常"
        else
            print_status "ERROR" "本地部署: 异常"
        fi
    fi
    
    if [ "$check_docker" = true ]; then
        if [ "$docker_healthy" = true ]; then
            print_status "SUCCESS" "Docker部署: 正常"
        else
            print_status "ERROR" "Docker部署: 异常"
        fi
    fi
    
    echo ""
    
    # 提供建议
    if [ "$check_local" = true ] && [ "$check_docker" = true ]; then
        if [ "$local_healthy" = true ] && [ "$docker_healthy" = true ]; then
            print_status "SUCCESS" "所有部署方式都正常运行"
        elif [ "$local_healthy" = true ]; then
            print_status "INFO" "建议: 本地部署正常，Docker部署需要检查"
        elif [ "$docker_healthy" = true ]; then
            print_status "INFO" "建议: Docker部署正常，本地部署需要检查"
        else
            print_status "ERROR" "建议: 所有部署方式都有问题，请检查配置"
        fi
    fi
}

# 运行主函数
main "$@"
