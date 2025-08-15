#!/usr/bin/env bash
set -euo pipefail

NS=selenium-grid

echo "🧹 清理 Selenium Grid 环境..."

echo "[1/6] 删除 KEDA ScaledObject..."
kubectl delete -f keda-metricsapi-scaledobject.yaml --ignore-not-found || true

       echo "[2/5] 删除 Grid Metrics Exporter..."
       kubectl delete -f grid-metrics-exporter.yaml --ignore-not-found || true
       kubectl delete -f grid-metrics-exporter-configmap.yaml --ignore-not-found || true

       echo "[3/5] 删除 Chrome Node Deployment..."
       kubectl delete -f node-deployment.yaml --ignore-not-found || true

       echo "[4/5] 删除 Hub Deployment 和 Service..."
       kubectl delete -f node-deployment.yaml -f hub-service.yaml --ignore-not-found || true

       echo "[5/5] 删除 Namespace..."
kubectl delete -f namespace.yaml --ignore-not-found || true

echo "✅ 清理完成！"

echo -n "是否删除 kind 集群？(y/N): "
read -r ans || true
if [[ "${ans:-N}" == "y" || "${ans:-N}" == "Y" ]]; then
    echo "删除 kind 集群..."
    kind delete cluster --name selenium-cluster || true
    echo "✅ kind 集群已删除"
fi

