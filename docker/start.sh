#!/bin/bash

# tinyproxy Grid 启动管理脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"
}

show_help() {
    cat << EOF
🌐 tinyproxy多节点Selenium Grid 管理脚本

用法: $0 [命令]

命令:
  start    启动Grid服务
  stop     停止Grid服务  
  restart  重启Grid服务
  status   查看Grid状态
  logs     查看实时日志
  test     运行测试验证
  build    构建Chrome镜像
  setup    生成新配置
  clean    清理所有资源

示例:
  $0 start     # 启动服务
  $0 test      # 测试代理
  $0 logs      # 查看日志
EOF
}

check_requirements() {
    log "检查环境要求..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! command -v "docker compose" &> /dev/null; then
        error "Docker Compose未安装"
        exit 1
    fi
    
    if [ ! -f "proxies.txt" ]; then
        warn "代理配置文件 proxies.txt 不存在"
        warn "请先配置代理IP或运行: $0 setup"
        exit 1
    fi
}

start_grid() {
    log "🚀 启动tinyproxy Grid..."
    
    check_requirements
    
    # 检查配置文件
    if [ ! -f "docker-compose.yml" ]; then
        warn "Docker Compose配置不存在，正在生成..."
        python3 setup.py
    fi
    
    # 检查镜像
    if ! docker images | grep -q "chrome-tinyproxy-node"; then
        warn "tinyproxy镜像不存在，正在构建..."
        ./build.sh
    fi
    
    # 启动服务
    docker compose up -d
    
    log "⏳ 等待服务启动..."
    sleep 15
    
    # 检查状态
    if curl -s http://localhost:4444/status > /dev/null 2>&1; then
        log "✅ Grid启动成功"
        log "📊 Grid控制台: http://localhost:4444/ui"
        
        # 显示架构信息
        show_architecture_status
    else
        error "❌ Grid启动失败"
        exit 1
    fi
}

stop_grid() {
    log "🛑 停止Grid服务..."
    docker compose down
    log "✅ 服务已停止"
}

restart_grid() {
    log "🔄 重启Grid服务..."
    docker compose restart
    log "✅ 服务已重启"
}

show_status() {
    log "📊 Grid状态信息..."
    
    echo ""
    echo "=== Docker容器状态 ==="
    docker compose ps
    
    echo ""
    echo "=== Grid状态 ==="
    if curl -s http://localhost:4444/status > /dev/null 2>&1; then
        echo "Grid运行正常 ✅"
        echo "控制台: http://localhost:4444/ui"
        
        # 获取节点数量
        local nodes=$(docker compose ps | grep chrome-node | wc -l)
        echo "活跃节点: $nodes"
        
        show_architecture_status
    else
        echo "Grid未运行 ❌"
    fi
}

show_architecture_status() {
    echo ""
    echo "🏗️  当前架构 (tinyproxy - 极小开销):"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│  每个Chrome Node (~2MB tinyproxy开销)                   │"
    echo "│  ┌─────────────┐        ┌──────────────────────┐       │"
    echo "│  │   Chrome    │───────▶│  tinyproxy (8888)    │───────┼──▶ 上游代理"
    echo "│  │  (无感知)    │        │   (处理认证)          │       │"
    echo "│  └─────────────┘        └──────────────────────┘       │"
    echo "└─────────────────────────────────────────────────────────┘"
}

show_logs() {
    log "📋 显示实时日志..."
    docker compose logs -f
}

run_test() {
    log "🧪 运行代理测试..."
    
    if [ ! -f "test.py" ]; then
        create_test_script
    fi
    
    python3 test.py
}

create_test_script() {
    log "创建测试脚本..."
    
    cat > test.py << 'EOF'
#!/usr/bin/env python3
"""
tinyproxy Grid 测试脚本
"""

import concurrent.futures
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_single_session(session_id: int):
    """测试单个会话"""
    result = {'session_id': session_id, 'success': False, 'ip_info': None, 'error': None}
    
    driver = None
    try:
        print(f"🚀 启动会话 {session_id}...")
        
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Remote(
            command_executor="http://localhost:4444/wd/hub",
            options=options
        )
        
        print(f"📍 会话 {session_id} 获取IP信息...")
        driver.get("http://httpbin.org/ip")
        time.sleep(2)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        result['ip_info'] = body_text.strip()
        result['success'] = True
        
        print(f"✅ 会话 {session_id} 完成")
        
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ 会话 {session_id} 失败: {e}")
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return result

def main():
    print("🌐 tinyproxy Grid测试")
    print("=" * 60)
    
    # 检查Grid状态
    import requests
    try:
        response = requests.get("http://localhost:4444/status", timeout=10)
        if response.status_code != 200:
            print("❌ Grid不可用")
            return
    except:
        print("❌ Grid不可用")
        return
    
    print("✅ Grid运行正常")
    
    num_sessions = 3
    print(f"🚀 启动 {num_sessions} 个并发会话...")
    
    start_time = time.time()
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_sessions) as executor:
        futures = [executor.submit(test_single_session, i + 1) for i in range(num_sessions)]
        
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    end_time = time.time()
    
    # 分析结果
    print(f"\n📊 测试结果 (耗时: {end_time - start_time:.2f}秒):")
    print("=" * 60)
    
    successful = [r for r in results if r['success']]
    print(f"✅ 成功会话: {len(successful)}/{len(results)}")
    
    for result in successful:
        try:
            data = json.loads(result['ip_info'])
            ip = data.get('origin', 'unknown')
            print(f"会话 {result['session_id']}: IP {ip}")
        except:
            print(f"会话 {result['session_id']}: {result['ip_info'][:50]}...")
    
    print("\n💡 tinyproxy架构优势:")
    print("   ✅ 极小内存开销 (~2MB per node)")
    print("   ✅ Chrome完全无感知代理")
    print("   ✅ 无认证弹窗")
    print("   ✅ 易于扩展到数千节点")

if __name__ == "__main__":
    main()
EOF
    
    chmod +x test.py
}

setup_config() {
    log "⚙️  生成新配置..."
    python3 setup.py
}

build_image() {
    log "🔨 构建Chrome镜像..."
    ./build.sh
}

clean_all() {
    log "🧹 清理所有资源..."
    
    read -p "确定要清理所有Docker资源吗？(y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        docker compose down --remove-orphans --volumes
        docker rmi chrome-tinyproxy-node:latest 2>/dev/null || true
        log "✅ 清理完成"
    else
        log "取消清理"
    fi
}

# 主程序
case "${1:-}" in
    start)
        start_grid
        ;;
    stop)
        stop_grid
        ;;
    restart)
        restart_grid
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        log "🧪 运行代理验证测试..."
        if [ -f "verify.py" ]; then
            python3 verify.py
        else
            error "❌ 找不到 verify.py 测试脚本"
            exit 1
        fi
        ;;
    setup)
        setup_config
        ;;
    build)
        build_image
        ;;
    clean)
        clean_all
        ;;
    -h|--help|help)
        show_help
        ;;
    "")
        warn "请指定命令，使用 --help 查看帮助"
        exit 1
        ;;
    *)
        error "未知命令: $1"
        show_help
        exit 1
        ;;
esac