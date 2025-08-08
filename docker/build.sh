#!/bin/bash

# 构建tinyproxy Chrome节点镜像

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"
}

# 检查必要文件
check_files() {
    local files=("Dockerfile" "custom-entrypoint.sh" "setup-tinyproxy.sh" "tinyproxy.conf.template")
    
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
