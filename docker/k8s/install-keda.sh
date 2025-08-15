#!/usr/bin/env bash
set -euo pipefail

echo "🚀 安装 KEDA (Kubernetes Event-driven Autoscaling)..."
echo ""

# 检查 helm 是否可用
if ! command -v helm &> /dev/null; then
    echo "❌ 错误: helm 未安装或不在 PATH 中"
    echo "请先安装 Helm: https://helm.sh/docs/intro/install/"
    exit 1
fi

# 检查集群连接
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ 错误: 无法连接到 Kubernetes 集群"
    exit 1
fi

echo "✅ 集群连接正常"
echo ""

# 添加 KEDA Helm 仓库
echo "📦 添加 KEDA Helm 仓库..."
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
echo "✅ KEDA 仓库添加完成"
echo ""

# 安装 KEDA
echo "🔧 安装 KEDA..."
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
    --wait \
    --timeout=300s

echo ""
echo "✅ KEDA 安装完成！"
echo ""

# 验证安装
echo "🔍 验证 KEDA 安装..."
kubectl -n keda get pods
echo ""

echo "📝 下一步操作:"
echo "1. 应用扩容配置: kubectl apply -f keda-metricsapi-scaledobject.yaml"
echo "2. 检查扩容状态: kubectl -n selenium-grid get scaledobject"
echo "3. 测试扩容功能: python3 test_scaling.py"
echo ""
echo "📚 查看 KEDA 状态:"
echo "   kubectl -n keda get pods"
echo "   kubectl -n keda logs -f deployment/keda-operator"
