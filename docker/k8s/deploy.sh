#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
NAMESPACE="selenium-grid"

echo "🚀 开始部署 Selenium Grid on Kubernetes..."
echo "📍 工作目录: $HERE"
echo "🏷️  命名空间: $NAMESPACE"
echo ""

# 检查 kubectl 是否可用
if ! command -v kubectl &> /dev/null; then
    echo "❌ 错误: kubectl 未安装或不在 PATH 中"
    exit 1
fi

# 检查集群连接
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ 错误: 无法连接到 Kubernetes 集群"
    exit 1
fi

echo "✅ 集群连接正常"
echo ""

echo "[1/7] 📦 创建命名空间"
kubectl apply -f "$HERE/namespace.yaml"
echo "✅ 命名空间创建完成"
echo ""

echo "[2/7] 🎯 部署 Selenium Hub"
kubectl apply -f "$HERE/hub-deployment.yaml"
kubectl apply -f "$HERE/hub-service.yaml"
echo "✅ Hub 配置应用完成"
echo ""

echo "[3/7] 🌐 部署 Chrome Node"
kubectl apply -f "$HERE/node-deployment.yaml"
echo "✅ Chrome Node 配置应用完成"
echo ""

echo "[4/7] 📊 部署指标导出器"
kubectl apply -f "$HERE/grid-metrics-exporter-configmap.yaml"
kubectl apply -f "$HERE/grid-metrics-exporter.yaml"
echo "✅ 指标导出器配置应用完成"
echo ""

echo "[5/7] ⏳ 等待部署完成..."
echo "   等待 Hub 就绪..."
kubectl -n $NAMESPACE rollout status deploy/selenium-hub --timeout=300s || {
    echo "⚠️  Hub 部署超时，检查状态..."
    kubectl -n $NAMESPACE describe deploy/selenium-hub
    exit 1
}

echo "   等待 Chrome Node 就绪..."
kubectl -n $NAMESPACE rollout status deploy/chrome-node --timeout=300s || {
    echo "⚠️  Chrome Node 部署超时，检查状态..."
    kubectl -n $NAMESPACE describe deploy/chrome-node
    exit 1
}

echo "   等待指标导出器就绪..."
kubectl -n $NAMESPACE rollout status deploy/grid-metrics-exporter --timeout=300s || {
    echo "⚠️  指标导出器部署超时，检查状态..."
    kubectl -n $NAMESPACE describe deploy/grid-metrics-exporter
    exit 1
}

echo "✅ 所有部署完成"
echo ""

echo "[6/7] 📋 查看资源状态"
kubectl -n $NAMESPACE get all -o wide
echo ""

echo "[7/7] 🔍 检查服务状态"
echo "📊 Pod 状态:"
kubectl -n $NAMESPACE get pods -o wide
echo ""
echo "🌐 服务状态:"
kubectl -n $NAMESPACE get svc -o wide
echo ""

echo "🎉 部署完成！"
echo ""
echo "📋 访问信息:"
echo "🔗 Hub Web UI: http://172.16.1.129:30444"
echo "🔗 Hub GraphQL: http://172.16.1.129:30444/graphql"
echo ""
echo "📝 下一步操作:"
echo "1. 安装 KEDA: ./install-keda.sh"
echo "2. 应用扩容配置: kubectl apply -f keda-metricsapi-scaledobject.yaml"
echo "3. 测试扩容功能: python3 test_scaling.py"
echo ""
echo "📚 查看日志:"
echo "   Hub: kubectl -n $NAMESPACE logs -f deploy/selenium-hub"
echo "   Node: kubectl -n $NAMESPACE logs -f deploy/chrome-node"
echo "   指标导出器: kubectl -n $NAMESPACE logs -f deploy/grid-metrics-exporter"

