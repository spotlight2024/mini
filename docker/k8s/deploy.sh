#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

usage() {
    cat <<'EOF'
Usage: ./deploy.sh [options]

Options:
  --cleanup-first          部署前执行 cleanup.sh（保留 kind 集群）
  --skip-image-load        不自动 kind load 镜像，需提前手动导入
  --load-image IMAGE       额外指定需要导入的镜像，可重复使用
  --port-forward           部署完成后自动执行 kubectl port-forward 暴露 Grafana/Prometheus
  --expose-nodeport        通过宿主机 iptables 将 NodePort (32000/32001) 暴露到宿主机 80/90（需要 root）
  --help                   显示帮助

示例：
  ./deploy.sh --cleanup-first --skip-image-load
EOF
}

CLEANUP_FIRST=false
LOAD_IMAGES=true
EXTRA_IMAGES=()
ENABLE_PORT_FORWARD=false
ENABLE_NODEPORT_EXPOSE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cleanup-first)
            CLEANUP_FIRST=true
            ;;
        --skip-image-load)
            LOAD_IMAGES=false
            ;;
        --load-image)
            shift || { echo "Missing argument for --load-image" >&2; usage; exit 1; }
            EXTRA_IMAGES+=("$1")
            ;;
        --port-forward)
            ENABLE_PORT_FORWARD=true
            ;;
        --expose-nodeport)
            ENABLE_NODEPORT_EXPOSE=true
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
    shift || break
done

echo "🚀 部署 Selenium Grid on Kubernetes..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
CLUSTER_NAME="selenium-cluster"
NAMESPACE="selenium-grid"

echo "[1/9] 检查环境"
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl 未安装${NC}"
    exit 1
fi

if ! command -v kind &> /dev/null; then
    echo -e "${RED}❌ kind 未安装${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"

if ${CLEANUP_FIRST}; then
    echo "[0/9] 预清理历史资源"
    if kind get clusters | grep -q "${CLUSTER_NAME}"; then
        echo "   检测到现有 kind 集群，导出 kubeconfig 并执行 cleanup..."
        kind export kubeconfig --name "${CLUSTER_NAME}"
        "${HERE}/cleanup.sh" --skip-kind-delete
    else
        echo "   未发现名为 ${CLUSTER_NAME} 的 kind 集群，跳过 cleanup"
    fi
    echo ""
fi

echo "[2/9] 检查并创建 kind 集群"
if kind get clusters | grep -q "${CLUSTER_NAME}"; then
    echo "   集群 ${CLUSTER_NAME} 已存在，正在连接..."
    kind export kubeconfig --name "${CLUSTER_NAME}"
    echo -e "${GREEN}✅ 已连接到现有集群${NC}"
else
    echo "   集群 ${CLUSTER_NAME} 不存在，正在创建..."
    if [ -f "kind-config.yaml" ]; then
        echo "   使用配置文件创建集群..."
        kind create cluster --name "${CLUSTER_NAME}" --config kind-config.yaml
    else
        echo "   使用默认配置创建集群..."
        kind create cluster --name "${CLUSTER_NAME}"
    fi
    echo -e "${GREEN}✅ 集群创建完成${NC}"
fi

# 等待集群就绪
echo "   等待集群就绪..."
sleep 15

# 验证集群连接
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ 无法连接到 Kubernetes 集群${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 集群连接正常${NC}"

if ${LOAD_IMAGES}; then
    echo "[3/9] 加载必要的 Docker 镜像到 kind 集群"

    REQUIRED_IMAGES=("chrome-tinyproxy-node:latest")
    OPTIONAL_IMAGES=(
        "selenium/hub:latest"
        "python:3.11-slim"
        "ghcr.io/kedacore/keda:2.17.2"
        "ghcr.io/kedacore/keda-admission-webhooks:2.17.2"
        "ghcr.io/kedacore/keda-metrics-apiserver:2.17.2"
    )

    load_image() {
        local image="$1"
        local required="$2"
        if ! docker image inspect "$image" >/dev/null 2>&1; then
            if [[ "$required" == "true" ]]; then
                echo -e "${RED}❌ 必需镜像 $image 不存在，请先构建/拉取并手动执行 kind load${NC}"
                echo "   示例: docker pull $image && kind load docker-image $image --name ${CLUSTER_NAME}"
                exit 1
            else
                echo -e "${YELLOW}⚠️  可选镜像 $image 不存在，将依赖集群自行拉取${NC}"
                return
            fi
        fi

        echo "   加载镜像: $image"
        kind load docker-image "$image" --name "${CLUSTER_NAME}"
    }

    for image in "${REQUIRED_IMAGES[@]}"; do
        load_image "$image" true
    done

    for image in "${OPTIONAL_IMAGES[@]}"; do
        load_image "$image" false
    done

    for image in "${EXTRA_IMAGES[@]}"; do
        load_image "$image" false
    done

    echo -e "${GREEN}✅ 镜像加载步骤完成${NC}"
else
    echo "[3/9] 跳过镜像加载 (使用 --skip-image-load)"
    echo "   请确保下列镜像已手动导入 kind:"
    echo "   - chrome-tinyproxy-node:latest (必需)"
    echo "   - selenium/hub:latest"
    echo "   - python:3.11-slim"
    echo "   - ghcr.io/kedacore/keda:2.17.2 (及其子组件)"
fi

# 函数: 配置 port-forward，运行在后台
start_port_forward() {
    local svc=$1
    local local_port=$2
    local target_port=$3
    local log_file=$4
    echo "   启动 port-forward: ${svc} -> localhost:${local_port}"
    nohup kubectl -n monitoring port-forward --address 0.0.0.0 "svc/${svc}" "${local_port}:${target_port}" \
        >"${log_file}" 2>&1 &
    local pid=$!
    echo "     PID=${pid}, logs=${log_file}"
}

# 函数: 利用 iptables 将 NodePort 暴露到宿主机固定端口
expose_nodeport() {
    local external_port=$1
    local node_port=$2
    local svc_name=$3
    echo "   暴露 ${svc_name} NodePort ${node_port} -> 宿主机端口 ${external_port}"
    sudo iptables -t nat -C PREROUTING -p tcp --dport "${external_port}" -j REDIRECT --to-port "${node_port}" 2>/dev/null || \
        sudo iptables -t nat -A PREROUTING -p tcp --dport "${external_port}" -j REDIRECT --to-port "${node_port}"
    sudo iptables -t nat -C OUTPUT -p tcp --dport "${external_port}" -j REDIRECT --to-port "${node_port}" 2>/dev/null || \
        sudo iptables -t nat -A OUTPUT -p tcp --dport "${external_port}" -j REDIRECT --to-port "${node_port}"
}

echo "[4/9] 应用命名空间"
kubectl apply -f "$HERE/namespace.yaml" | cat

echo "[4.1/9] 配置 Selenium Logging & Tracing"
kubectl apply -f "$HERE/selenium-observability-configmap.yaml" | cat

echo "[5/9] 应用 NAS 存储配置"
kubectl apply -f "$HERE/chrome-nas-storageclass.yaml" | cat
kubectl apply -f "$HERE/chrome-nas-pv.yaml" | cat
kubectl apply -f "$HERE/chrome-nas-pvc.yaml" | cat

echo "[6/9] 应用 Selenium Grid 组件"
echo "   部署 Hub..."
kubectl apply -f "$HERE/hub-deployment.yaml" -f "$HERE/hub-service.yaml" | cat

echo "   部署 Chrome Node..."
kubectl apply -f "$HERE/node-deployment.yaml" | cat

echo "   部署指标导出器..."
kubectl apply -f "$HERE/grid-metrics-exporter-configmap.yaml" | cat
kubectl apply -f "$HERE/grid-metrics-exporter.yaml" | cat

echo "   部署 OpenTelemetry Collector..."
kubectl apply -f "$HERE/otel-collector.yaml" | cat

echo "   部署 Jaeger 全量节点..."
kubectl apply -f "$HERE/jaeger.yaml" | cat

echo "[7/9] 等待部署完成"
echo "   等待 Hub 就绪..."
kubectl -n ${NAMESPACE} wait --for=condition=ready pod -l app=selenium-hub --timeout=120s || {
    echo -e "${YELLOW}⚠️  Hub 启动超时，继续检查状态...${NC}"
}

echo "   等待 Chrome Node 就绪..."
kubectl -n ${NAMESPACE} wait --for=condition=ready pod -l app=chrome-node --timeout=180s || {
    echo -e "${YELLOW}⚠️  Chrome Node 启动超时，继续检查状态...${NC}"
}

echo "   等待指标导出器就绪..."
kubectl -n ${NAMESPACE} wait --for=condition=ready pod -l app=grid-metrics-exporter --timeout=120s || {
    echo -e "${YELLOW}⚠️  指标导出器启动超时，继续检查状态...${NC}"
}

echo "[8/9] 安装 KEDA 自动扩容"
if command -v helm &> /dev/null; then
    echo "   检查 KEDA 是否已安装..."
    
    # 清理可能存在的失败安装
    if kubectl get namespace keda &> /dev/null; then
        echo "   清理之前的 KEDA 安装..."
        helm uninstall keda -n keda --ignore-not-found || true
        kubectl delete namespace keda --force --grace-period=0 --ignore-not-found || true
        sleep 10
    fi
    
    echo "   添加 KEDA Helm 仓库..."
    helm repo add kedacore https://kedacore.github.io/charts
    helm repo update
    
    echo "   安装 KEDA..."
    helm install keda kedacore/keda \
        --namespace keda \
        --create-namespace \
        --set image.pullPolicy=IfNotPresent \
        --set logging.operator.level=info \
        --set logging.webhooks.level=info \
        --set logging.metricsApiServer.level=info \
        --set operator.resources.requests.cpu=100m \
        --set operator.resources.requests.memory=100Mi \
        --set operator.resources.limits.cpu=1000m \
        --set operator.resources.limits.memory=1000Mi \
        --set metricsApiServer.resources.requests.cpu=100m \
        --set metricsApiServer.resources.requests.memory=100Mi \
        --set metricsApiServer.resources.limits.cpu=1000m \
        --set metricsApiServer.resources.limits.memory=1000Mi \
        --set admissionWebhooks.resources.requests.cpu=100m \
        --set admissionWebhooks.resources.requests.memory=100Mi \
        --set admissionWebhooks.resources.limits.cpu=1000m \
        --set admissionWebhooks.resources.limits.memory=1000Mi
    
    echo "   等待 KEDA 就绪..."
    kubectl -n keda wait --for=condition=ready pod -l app.kubernetes.io/name=keda --timeout=300s || {
        echo -e "${YELLOW}⚠️  KEDA 启动超时，但继续配置扩容...${NC}"
    }
    
    echo "   配置自动扩容..."
    kubectl apply -f "$HERE/keda-metricsapi-scaledobject.yaml" | cat
    echo -e "${GREEN}✅ 自动扩容配置完成${NC}"
else
    echo -e "${YELLOW}⚠️  Helm 未安装，跳过 KEDA 安装${NC}"
fi

echo "[9/9] 查看资源状态"
echo "📊 Pod 状态:"
kubectl -n ${NAMESPACE} get pods | cat

echo ""
echo "🌐 服务状态:"
kubectl -n ${NAMESPACE} get services | cat

echo ""
echo "📦 部署状态:"
kubectl -n ${NAMESPACE} get deployments | cat

echo ""
echo "💾 存储状态:"
kubectl -n ${NAMESPACE} get pvc | cat
kubectl get pv -l type=chrome-nas | cat

if command -v helm &> /dev/null && kubectl get namespace keda &> /dev/null; then
    echo ""
    echo "🚀 扩容状态:"
    kubectl -n ${NAMESPACE} get scaledobject | cat
fi

echo ""
echo -e "${GREEN}📋 部署完成！${NC}"
echo -e "${GREEN}🔗 Hub 访问地址: http://172.16.1.129:30444${NC}"
echo -e "${GREEN}🔗 Hub GraphQL: http://172.16.1.129:30444/graphql${NC}"

echo ""
echo -e "${BLUE}📝 下一步：${NC}"
echo -e "${GREEN}1. 测试扩容功能: python3 test_scaling.py${NC}"
echo -e "${GREEN}2. 查看日志: kubectl -n ${NAMESPACE} logs -f deploy/selenium-hub${NC}"
echo -e "${GREEN}3. 监控扩容: kubectl -n ${NAMESPACE} get scaledobject -w${NC}"

echo ""
echo -e "${BLUE}📚 查看日志命令:${NC}"
echo -e "${GREEN}   Hub: kubectl -n ${NAMESPACE} logs -f deploy/selenium-hub${NC}"
echo -e "${GREEN}   Node: kubectl -n ${NAMESPACE} logs -f deploy/chrome-node${NC}"
echo -e "${GREEN}   指标导出器: kubectl -n ${NAMESPACE} logs -f deploy/grid-metrics-exporter${NC}"

echo ""
echo -e "${BLUE}🔧 故障排除:${NC}"
echo -e "${GREEN}   检查 Pod 状态: kubectl -n ${NAMESPACE} describe pod <pod-name>${NC}"
echo -e "${GREEN}   检查事件: kubectl -n ${NAMESPACE} get events --sort-by=.metadata.creationTimestamp${NC}"
echo -e "${GREEN}   检查存储: kubectl -n ${NAMESPACE} describe pvc chrome-nas-pvc${NC}"
echo -e "${GREEN}   检查扩容: kubectl -n ${NAMESPACE} get scaledobject${NC}"

echo ""
echo -e "${BLUE}🗑️  清理命令:${NC}"
echo -e "${GREEN}   清理环境: ./cleanup.sh${NC}"
echo -e "${GREEN}   删除集群: kind delete cluster --name ${CLUSTER_NAME}${NC}"

echo ""
if ${ENABLE_PORT_FORWARD}; then
    echo ""
    echo "[10/9] 配置本地访问 (port-forward)"
    start_port_forward monitoring-grafana 30080 80 /tmp/grafana-port-forward.log
    start_port_forward monitoring-kube-prometheus-prometheus 30090 9090 /tmp/prometheus-port-forward.log
    echo -e "${GREEN}✅ Grafana: http://127.0.0.1:30080 (admin/prom-operator)${NC}"
    echo -e "${GREEN}✅ Prometheus: http://127.0.0.1:30090${NC}"
fi

if ${ENABLE_NODEPORT_EXPOSE}; then
    echo ""
    echo "[10/9] 配置宿主机端口映射 (NodePort)"
    expose_nodeport 30080 32000 monitoring-grafana
    expose_nodeport 30090 32001 monitoring-kube-prometheus-prometheus
    echo -e "${GREEN}✅ Grafana: http://<宿主机IP>:30080 (admin/prom-operator)${NC}"
    echo -e "${GREEN}✅ Prometheus: http://<宿主机IP>:30090${NC}"
fi

echo ""
echo -e "${GREEN}✨ 现在可以运行测试脚本验证所有功能！${NC}"
