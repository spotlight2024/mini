#!/bin/bash

# 测试执行顺序的脚本

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

print_message $BLUE "=== 测试自定义 Selenium Chrome 镜像执行顺序 ==="
echo ""

# 构建镜像
print_message $YELLOW "1. 构建自定义镜像..."
docker compose -f docker-compose.custom-selenium.yml build --no-cache
print_message $GREEN "✓ 镜像构建完成"
echo ""

# 启动容器并实时查看日志
print_message $YELLOW "2. 启动容器并监控执行顺序..."
echo "注意: 请观察日志中的执行阶段标记"
echo ""

# 启动容器
docker compose -f docker-compose.custom-selenium.yml up -d custom-selenium-chrome

# 等待容器启动并查看日志
sleep 3
print_message $BLUE "=== 容器启动日志 (显示执行顺序) ==="
docker compose -f docker-compose.custom-selenium.yml logs custom-selenium-chrome

echo ""
print_message $GREEN "=== 执行顺序验证完成 ==="
echo ""
print_message $BLUE "预期执行顺序:"
echo "1. 自定义启动脚本包装器开始"
echo "2. 调用自定义启动脚本"
echo "3. 自定义启动脚本执行完成"
echo "4. 启动原始 Selenium Chrome 服务"
echo "5. Selenium 服务正常运行"
echo ""

# 检查服务状态
print_message $YELLOW "3. 验证 Selenium 服务状态..."
sleep 5
if curl -s http://localhost:4444/status > /dev/null; then
    print_message $GREEN "✓ Selenium 服务正常运行"
else
    print_message $RED "✗ Selenium 服务异常"
fi

echo ""
print_message $YELLOW "4. 查看自定义脚本日志..."
if docker compose -f docker-compose.custom-selenium.yml ps -q custom-selenium-chrome > /dev/null; then
    local container_id=$(docker compose -f docker-compose.custom-selenium.yml ps -q custom-selenium-chrome)
    if docker exec "$container_id" test -f /opt/scripts/logs/startup.log; then
        print_message $BLUE "自定义启动脚本日志:"
        docker exec "$container_id" cat /opt/scripts/logs/startup.log
    else
        print_message $YELLOW "自定义启动脚本日志文件不存在"
    fi
fi

echo ""
print_message $GREEN "=== 测试完成 ==="
print_message $YELLOW "使用以下命令查看实时日志:"
echo "docker compose -f docker-compose.custom-selenium.yml logs -f custom-selenium-chrome"
echo ""
print_message $YELLOW "使用以下命令停止容器:"
echo "docker compose -f docker-compose.custom-selenium.yml down" 