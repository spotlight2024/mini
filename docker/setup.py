#!/usr/bin/env python3
"""
tinyproxy多节点配置生成器
最优架构：Chrome + tinyproxy (极小资源开销)
"""

import re
import sys
from typing import List, Dict, Tuple

def parse_proxy_file(filename: str) -> List[Dict[str, str]]:
    """解析代理配置文件"""
    proxies = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析格式: username:password@host:port
                match = re.match(r'^([^:]+):([^@]+)@([^:]+):(\d+)$', line)
                if match:
                    username, password, host, port = match.groups()
                    proxies.append({
                        'username': username,
                        'password': password,
                        'host': host,
                        'port': port
                    })
                    print(f"✅ 解析代理 {len(proxies)}: {username}@{host}:{port}")
                else:
                    print(f"⚠️  第{line_num}行格式错误，跳过: {line}")
    
    except FileNotFoundError:
        print(f"❌ 找不到代理配置文件: {filename}")
        return []
    except Exception as e:
        print(f"❌ 读取代理配置文件出错: {e}")
        return []
    
    return proxies

def generate_docker_compose(proxies: List[Dict[str, str]], num_nodes: int) -> Tuple[str, int]:
    """生成Docker Compose配置"""
    
    # 确定实际节点数量
    actual_nodes = min(num_nodes, len(proxies)) if proxies else num_nodes
    
    compose_content = '''version: '3.8'

services:
  selenium-hub:
    image: selenium/hub:latest
    container_name: selenium-hub
    ports:
      - "4442:4442"
      - "4443:4443"
      - "4444:4444"
    environment:
      - SE_NODE_SESSION_TIMEOUT=300
      - SE_SESSION_REQUEST_TIMEOUT=300
      - SE_NODE_MAX_SESSIONS={}
    networks:
      - selenium-grid
    restart: unless-stopped

'''.format(actual_nodes * 2)

    # 生成Chrome节点
    for i in range(actual_nodes):
        node_num = i + 1
        
        # 配置代理环境变量
        if i < len(proxies):
            proxy = proxies[i]
            proxy_env = f'''      # 上游代理配置 - 节点{node_num}
      - PROXY_HOST={proxy['host']}
      - PROXY_PORT={proxy['port']}
      - PROXY_USERNAME={proxy['username']}
      - PROXY_PASSWORD={proxy['password']}'''
        else:
            proxy_env = f'''      # 无代理配置 - 节点{node_num} (直连)'''
        
        node_config = f'''  chrome-node-{node_num}:
    image: chrome-tinyproxy-node:latest
    container_name: chrome-node-{node_num}
    depends_on:
      - selenium-hub
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_NODE_MAX_SESSIONS=1
      - SE_NODE_OVERRIDE_MAX_SESSIONS=true
{proxy_env}
    networks:
      - selenium-grid
    shm_size: 2gb
    restart: unless-stopped
    # tinyproxy架构：极小资源开销
    mem_limit: 512m
    cpus: 0.5

'''
        compose_content += node_config

    # 添加网络配置
    compose_content += '''networks:
  selenium-grid:
    driver: bridge'''
    
    return compose_content, actual_nodes

def create_build_script():
    """创建构建脚本"""
    build_script = '''#!/bin/bash

# 构建tinyproxy Chrome节点镜像

set -e

GREEN='\\033[0;32m'
RED='\\033[0;31m'
NC='\\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"
}

# 检查必要文件
check_files() {
    local files=("Dockerfile" "entrypoint.sh" "setup-proxy.sh" "tinyproxy.conf.template" "supervisord.conf")
    
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            error "缺少文件: $file"
            exit 1
        fi
    done
}

# 构建镜像
build_image() {
    log "🔨 构建Chrome + tinyproxy镜像..."
    
    if docker build -t chrome-tinyproxy-node:latest . ; then
        log "✅ 镜像构建成功"
        
        # 显示镜像大小
        local size=$(docker images chrome-tinyproxy-node:latest --format "{{.Size}}")
        log "📦 镜像大小: $size"
    else
        error "❌ 镜像构建失败"
        exit 1
    fi
}

main() {
    log "🚀 构建tinyproxy架构镜像"
    check_files
    build_image
    log "🎉 构建完成！运行: ./start.sh 启动Grid"
}

main "$@"
'''
    
    with open('build.sh', 'w') as f:
        f.write(build_script)
    
    import os
    os.chmod('build.sh', 0o755)

def main():
    print("🚀 tinyproxy多节点配置生成器")
    print("=" * 50)
    print("💡 最优架构：Chrome + tinyproxy (极小资源开销 ~2MB)")
    print()
    
    # 读取代理配置
    proxy_file = input("请输入代理配置文件路径 (默认: proxies.txt): ").strip()
    if not proxy_file:
        proxy_file = "proxies.txt"
    
    proxies = parse_proxy_file(proxy_file)
    
    if not proxies:
        print("❌ 没有找到有效的代理配置")
        print("💡 提示：代理格式应为 username:password@host:port")
        sys.exit(1)
    
    print(f"✅ 成功解析 {len(proxies)} 个代理配置")
    
    # 获取节点数量
    default_nodes = len(proxies)
    try:
        num_nodes = input(f"请输入Chrome节点数量 (默认: {default_nodes}): ").strip()
        num_nodes = int(num_nodes) if num_nodes else default_nodes
        
        if num_nodes <= 0:
            raise ValueError("节点数量必须大于0")
            
    except ValueError as e:
        print(f"❌ 无效的节点数量: {e}")
        sys.exit(1)
    
    # 生成配置
    compose_config, actual_nodes = generate_docker_compose(proxies, num_nodes)
    
    # 写入配置文件
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_config)
    
    # 创建构建脚本
    create_build_script()
    
    print(f"\\n🎉 配置生成完成!")
    print(f"✅ Docker Compose: docker-compose.yml")
    print(f"✅ 构建脚本: build.sh")
    print(f"📊 实际节点数: {actual_nodes}")
    
    # 显示资源估算
    total_memory = actual_nodes * 2  # 每节点约2MB tinyproxy
    print(f"📈 资源估算:")
    print(f"   tinyproxy总内存: ~{total_memory}MB")
    print(f"   vs Squid总内存: ~{actual_nodes * 20}MB")
    print(f"   节省内存: ~{actual_nodes * 18}MB")
    
    if actual_nodes < num_nodes:
        print(f"⚠️  注意：代理数量({len(proxies)}) < 请求节点数({num_nodes})")
    
    print("\\n📋 下一步:")
    print("1. 构建镜像: ./build.sh")
    print("2. 启动服务: ./start.sh")
    print("3. 测试验证: ./test.sh")

if __name__ == "__main__":
    main()