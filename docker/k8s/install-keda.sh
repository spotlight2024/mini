#!/bin/bash

# Helper script to install or upgrade KEDA via Helm.
set -euo pipefail

NAMESPACE="keda"
RELEASE="keda"
CHART="kedacore/keda"
VERSION="2.15.0"

if ! command -v helm >/dev/null 2>&1; then
  echo "helm is required" >&2
  exit 1
fi

helm repo add kedacore https://kedacore.github.io/charts >/dev/null
helm repo update >/dev/null

kubectl get namespace "$NAMESPACE" >/dev/null 2>&1 || kubectl create namespace "$NAMESPACE"

helm upgrade --install "$RELEASE" "$CHART" \
  --namespace "$NAMESPACE" \
  --version "$VERSION" \
  --set metricsServer.enabled=true \
  --wait

echo "KEDA installed"
