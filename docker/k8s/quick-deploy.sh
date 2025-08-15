#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
NAMESPACE="selenium-grid"

echo "🚀 Selenium Grid 一键部署脚本"
echo "📍 工作目录: $HERE"
echo "🏷️  命名空间: $NAMESPACE"
echo ""

# 检查必要工具
check_prerequisites() {
    echo "🔍 检查前置条件..."
    
    if ! command -v kubectl &> /dev/null; then
        echo "❌ 错误: kubectl 未安装"
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        echo "❌ 错误: helm 未安装"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        echo "❌ 错误: 无法连接到 Kubernetes 集群"
        exit 1
    fi
    
    echo "✅ 前置条件检查通过"
    echo ""
}

# 部署 Selenium Grid
deploy_selenium_grid() {
    echo "📦 部署 Selenium Grid..."
    ./deploy.sh
    echo ""
}

# 安装 KEDA
install_keda() {
    echo "🔧 安装 KEDA..."
    ./install-keda.sh
    echo ""
}

# 应用扩容配置
apply_scaling_config() {
    echo "📊 应用扩容配置..."
    kubectl apply -f keda-metricsapi-scaledobject.yaml
    echo "✅ 扩容配置应用完成"
    echo ""
}

# 验证部署
verify_deployment() {
    echo "🔍 验证部署状态..."
    
    echo "📊 Pod 状态:"
    kubectl -n $NAMESPACE get pods -o wide
    echo ""
    
    echo "🌐 服务状态:"
    kubectl -n $NAMESPACE get svc -o wide
    echo ""
    
    echo "📈 扩容配置状态:"
    kubectl -n $NAMESPACE get scaledobject
    echo ""
    
    echo "🎯 KEDA 状态:"
    kubectl -n keda get pods
    echo ""
}

# 显示访问信息
show_access_info() {
    echo "🎉 部署完成！"
    echo ""
    echo "📋 访问信息:"
    echo "🔗 Hub Web UI: http://172.16.1.129:30444"
    echo "🔗 Hub GraphQL: http://172.16.1.129:30444/graphql"
    echo ""
    echo "📝 常用命令:"
    echo "   查看状态: kubectl -n $NAMESPACE get all"
    echo "   查看日志: kubectl -n $NAMESPACE logs -f deploy/selenium-hub"
    echo "   测试扩容: python3 test_scaling.py"
    echo "   清理环境: ./cleanup.sh"
    echo ""
}

# 主函数
main() {
    check_prerequisites
    deploy_selenium_grid
    install_keda
    apply_scaling_config
    verify_deployment
    show_access_info
}

# 执行主函数
main "$@"
