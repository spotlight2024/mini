#!/bin/bash

# 🧹 Selenium Grid 环境清理脚本
# 清理：所有部署、服务、存储、KEDA 等

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

NS="selenium-grid"

echo -e "${BLUE}🧹 清理 Selenium Grid 环境...${NC}"
echo ""

# 检查 kubectl 是否可用
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl 未安装${NC}"
    exit 1
fi

# 检查集群连接
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ 无法连接到 Kubernetes 集群${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/8] 🚀 删除 KEDA ScaledObject...${NC}"
kubectl delete -f keda-metricsapi-scaledobject.yaml --ignore-not-found || true
echo -e "${GREEN}✅ KEDA ScaledObject 已删除${NC}"

echo -e "${YELLOW}[2/8] 📊 删除 Grid Metrics Exporter...${NC}"
kubectl delete -f grid-metrics-exporter.yaml --ignore-not-found || true
kubectl delete -f grid-metrics-exporter-configmap.yaml --ignore-not-found || true
echo -e "${GREEN}✅ Grid Metrics Exporter 已删除${NC}"

echo -e "${YELLOW}[3/8] 🌐 删除 Chrome Node Deployment...${NC}"
kubectl delete -f node-deployment.yaml --ignore-not-found || true
echo -e "${GREEN}✅ Chrome Node Deployment 已删除${NC}"

echo -e "${YELLOW}[4/8] 🎯 删除 Hub Deployment 和 Service...${NC}"
kubectl delete -f hub-deployment.yaml --ignore-not-found || true
kubectl delete -f hub-service.yaml --ignore-not-found || true
echo -e "${GREEN}✅ Hub Deployment 和 Service 已删除${NC}"

echo -e "${YELLOW}[5/8] 💾 删除 NAS 存储配置...${NC}"
kubectl delete -f chrome-nas-pvc.yaml --ignore-not-found || true
kubectl delete -f chrome-nas-pv.yaml --ignore-not-found || true
kubectl delete -f chrome-nas-storageclass.yaml --ignore-not-found || true
echo -e "${GREEN}✅ NAS 存储配置已删除${NC}"

echo -e "${YELLOW}[6/8] 🚀 删除 KEDA 系统...${NC}"
if kubectl get namespace keda &> /dev/null; then
    if command -v helm &> /dev/null; then
        echo "   卸载 KEDA..."
        helm uninstall keda -n keda --ignore-not-found || true
        echo "   删除 KEDA 命名空间..."
        kubectl delete namespace keda --ignore-not-found || true
        echo -e "${GREEN}✅ KEDA 系统已删除${NC}"
    else
        echo -e "${YELLOW}⚠️  Helm 未安装，手动删除 KEDA 命名空间...${NC}"
        kubectl delete namespace keda --ignore-not-found || true
        echo -e "${GREEN}✅ KEDA 命名空间已删除${NC}"
    fi
else
    echo -e "${GREEN}✅ KEDA 未安装${NC}"
fi

echo -e "${YELLOW}[7/8] 🗂️  删除所有相关资源...${NC}"
# 强制删除所有 Pod、Service、Deployment
kubectl -n ${NS} delete all --all --force --grace-period=0 --ignore-not-found || true
echo -e "${GREEN}✅ 所有资源已删除${NC}"

echo -e "${YELLOW}[8/8] 🏷️  删除命名空间...${NC}"
kubectl delete namespace ${NS} --ignore-not-found || true
echo -e "${GREEN}✅ 命名空间已删除${NC}"

echo ""
echo -e "${GREEN}✅ 清理完成！${NC}"

# 清理 kind 集群选项
echo ""
echo -e "${BLUE}🔍 检查 kind 集群状态...${NC}"
if kubectl get nodes &> /dev/null; then
    echo -e "${YELLOW}是否删除 kind 集群？(y/N): ${NC}"
    read -r ans || true
    if [[ "${ans:-N}" == "y" || "${ans:-N}" == "Y" ]]; then
        echo -e "${YELLOW}删除 kind 集群...${NC}"
        kind delete cluster --name selenium-cluster || true
        echo -e "${GREEN}✅ kind 集群已删除${NC}"
    else
        echo -e "${GREEN}✅ kind 集群保留${NC}"
    fi
else
    echo -e "${GREEN}✅ 没有检测到 kind 集群${NC}"
fi

echo ""
echo -e "${BLUE}📋 清理总结:${NC}"
echo -e "${GREEN}✅ KEDA ScaledObject${NC}"
echo -e "${GREEN}✅ Grid Metrics Exporter${NC}"
echo -e "${GREEN}✅ Chrome Node Deployment${NC}"
echo -e "${GREEN}✅ Hub Deployment 和 Service${NC}"
echo -e "${GREEN}✅ NAS 存储配置${NC}"
echo -e "${GREEN}✅ KEDA 系统${NC}"
echo -e "${GREEN}✅ 所有相关资源${NC}"
echo -e "${GREEN}✅ 命名空间${NC}"

echo ""
echo -e "${GREEN}✨ 环境清理完成，可以重新运行 ./deploy.sh 进行部署！${NC}"

