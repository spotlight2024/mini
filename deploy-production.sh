#!/bin/bash

# Android Web自动化平台生产环境部署脚本
# 作者: SpotLight Team
# 版本: 1.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    log_info "检查Docker环境..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 检查系统要求
check_system_requirements() {
    log_info "检查系统要求..."
    
    # 检查内存
    total_mem=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
    if [ $total_mem -lt 8 ]; then
        log_warning "系统内存不足8GB，建议增加内存"
    fi
    
    # 检查磁盘空间
    available_space=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    if [ $available_space -lt 20 ]; then
        log_warning "磁盘空间不足20GB，建议清理空间"
    fi
    
    log_success "系统要求检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p nginx/ssl
    mkdir -p nginx/logs
    mkdir -p logs/selenium
    mkdir -p logs/android
    mkdir -p certs
    mkdir -p config
    mkdir -p monitoring/grafana/provisioning
    mkdir -p monitoring/grafana/dashboards
    mkdir -p scripts
    
    log_success "目录创建完成"
}

# 创建环境变量文件
create_env_file() {
    log_info "创建环境变量文件..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# 数据库配置
KONG_DB_PASSWORD=kong123
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=password123
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# API配置
JWT_SECRET=your-secret-key-here-$(date +%s)
API_RATE_LIMIT=1000
LOG_LEVEL=INFO

# 监控配置
GRAFANA_PASSWORD=admin123

# 扩缩容配置
SCALE_UP_THRESHOLD=80
SCALE_DOWN_THRESHOLD=30
MAX_NODES=20
MIN_NODES=3

# Chrome配置
CHROME_DRIVER_VERSION=
CHROME_DRIVER_DOWNLOAD_URL=
SE_INSTALL_CERTIFICATES=true

# Android设备配置
ADB_HOST=localhost
ADB_PORT=5037
DEVICE_POOL_SIZE=10
EOF
        log_success "环境变量文件创建完成"
    else
        log_warning "环境变量文件已存在，跳过创建"
    fi
}

# 创建Nginx配置
create_nginx_config() {
    log_info "创建Nginx配置..."
    
    cat > nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        server kong-gateway:8000;
    }
    
    upstream grafana_backend {
        server grafana:3000;
    }
    
    upstream prometheus_backend {
        server prometheus:9090;
    }
    
    upstream kibana_backend {
        server kibana:5601;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # API服务
        location /api/ {
            proxy_pass http://api_backend/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Grafana监控面板
        location /grafana/ {
            proxy_pass http://grafana_backend/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Prometheus指标
        location /prometheus/ {
            proxy_pass http://prometheus_backend/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Kibana日志
        location /kibana/ {
            proxy_pass http://kibana_backend/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # 健康检查
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF
    
    log_success "Nginx配置创建完成"
}

# 创建监控配置
create_monitoring_config() {
    log_info "创建监控配置..."
    
    # Prometheus配置
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'spotlight-api'
    static_configs:
      - targets: ['spotlight-api:8002']
    metrics_path: '/metrics'

  - job_name: 'selenium-hub'
    static_configs:
      - targets: ['selenium-hub:4444']
    metrics_path: '/metrics'

  - job_name: 'selenium-node'
    static_configs:
      - targets: ['selenium-node:5555']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'mongodb'
    static_configs:
      - targets: ['mongo:27017']
EOF

    # AlertManager配置
    cat > monitoring/alertmanager.yml << EOF
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alertmanager@example.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'team-email'

receivers:
  - name: 'team-email'
    email_configs:
      - to: 'team@example.com'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
EOF

    # Logstash配置
    cat > monitoring/logstash.conf << EOF
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "spotlight-api" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "spotlight-logs-%{+YYYY.MM.dd}"
  }
}
EOF

    log_success "监控配置创建完成"
}

# 创建运维脚本
create_scripts() {
    log_info "创建运维脚本..."
    
    # 自动扩缩容脚本
    cat > scripts/auto-scale.sh << 'EOF'
#!/bin/bash

# 获取当前负载
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.2f", $3/$2 * 100.0)}')
QUEUE_LENGTH=$(redis-cli llen automation_queue)

# 扩容条件
if (( $(echo "$CPU_USAGE > 80" | bc -l) )) || (( $(echo "$MEMORY_USAGE > 80" | bc -l) )) || [ $QUEUE_LENGTH -gt 100 ]; then
    echo "触发扩容..."
    docker-compose -f docker-compose-production.yml up -d --scale selenium-node=+1
    docker-compose -f docker-compose-production.yml up -d --scale spotlight-api=+1
fi

# 缩容条件
if (( $(echo "$CPU_USAGE < 30" | bc -l) )) && (( $(echo "$MEMORY_USAGE < 30" | bc -l) )) && [ $QUEUE_LENGTH -lt 10 ]; then
    echo "触发缩容..."
    docker-compose -f docker-compose-production.yml up -d --scale selenium-node=-1
    docker-compose -f docker-compose-production.yml up -d --scale spotlight-api=-1
fi
EOF

    # 健康检查脚本
    cat > scripts/health-check.sh << 'EOF'
#!/bin/bash

# 检查API服务
check_api() {
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health)
    if [ $response -eq 200 ]; then
        echo "✅ API服务正常"
    else
        echo "❌ API服务异常: $response"
        return 1
    fi
}

# 检查Selenium Hub
check_hub() {
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4444/status)
    if [ $response -eq 200 ]; then
        echo "✅ Selenium Hub正常"
    else
        echo "❌ Selenium Hub异常: $response"
        return 1
    fi
}

# 检查Redis
check_redis() {
    if redis-cli ping | grep -q "PONG"; then
        echo "✅ Redis正常"
    else
        echo "❌ Redis异常"
        return 1
    fi
}

# 执行检查
echo "🔍 开始健康检查..."
check_api && check_hub && check_redis
echo "✅ 健康检查完成"
EOF

    # 设置执行权限
    chmod +x scripts/auto-scale.sh
    chmod +x scripts/health-check.sh
    
    log_success "运维脚本创建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 拉取镜像
    log_info "拉取Docker镜像..."
    docker-compose -f docker-compose-production.yml pull
    
    # 启动服务
    log_info "启动所有服务..."
    docker-compose -f docker-compose-production.yml up -d
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    # 等待数据库服务
    log_info "等待数据库服务..."
    sleep 30
    
    # 等待API服务
    log_info "等待API服务..."
    for i in {1..60}; do
        if curl -f http://localhost:8002/health &> /dev/null; then
            log_success "API服务就绪"
            break
        fi
        sleep 5
    done
    
    # 等待监控服务
    log_info "等待监控服务..."
    sleep 30
    
    log_success "所有服务就绪"
}

# 显示服务状态
show_status() {
    log_info "显示服务状态..."
    
    echo ""
    echo "=========================================="
    echo "          服务访问地址"
    echo "=========================================="
    echo "Nginx负载均衡器:     http://localhost:80"
    echo "Kong Admin:         http://localhost:8001"
    echo "SpotLight API:      http://localhost:8002"
    echo "Selenium Hub:       http://localhost:4444"
    echo "Grafana监控面板:     http://localhost:3000 (admin/admin123)"
    echo "Prometheus指标:     http://localhost:9090"
    echo "Kibana日志:         http://localhost:5601"
    echo "Jaeger链路追踪:     http://localhost:16686"
    echo "MinIO文件管理:      http://localhost:9001 (minioadmin/minioadmin123)"
    echo "=========================================="
    echo ""
    
    # 显示容器状态
    docker-compose -f docker-compose-production.yml ps
}

# 主函数
main() {
    echo "=========================================="
    echo "    Android Web自动化平台部署脚本"
    echo "=========================================="
    echo ""
    
    check_docker
    check_system_requirements
    create_directories
    create_env_file
    create_nginx_config
    create_monitoring_config
    create_scripts
    start_services
    wait_for_services
    show_status
    
    echo ""
    log_success "部署完成！"
    echo ""
    echo "使用以下命令管理服务："
    echo "  查看状态: docker-compose -f docker-compose-production.yml ps"
    echo "  查看日志: docker-compose -f docker-compose-production.yml logs -f"
    echo "  停止服务: docker-compose -f docker-compose-production.yml down"
    echo "  重启服务: docker-compose -f docker-compose-production.yml restart"
    echo ""
    echo "运维脚本："
    echo "  健康检查: ./scripts/health-check.sh"
    echo "  自动扩缩容: ./scripts/auto-scale.sh"
    echo ""
}

# 执行主函数
main "$@" 