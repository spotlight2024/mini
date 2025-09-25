# Selenium Grid on Kubernetes 运维部署指南

## 🏗️ 架构概述

基于 KEDA 的 Selenium Grid 自动扩容集群，实现"活跃会话数 + 2"的智能扩容逻辑。

### 核心组件
- **Selenium Hub**: Grid 控制中心，管理会话分发和负载均衡
- **Chrome Nodes**: Chrome 浏览器节点，支持 VNC 和 tinyproxy 透明代理
- **KEDA**: Kubernetes Event-driven Autoscaling 自动扩容控制器
- **自定义指标导出器**: 实时监控活跃会话数，提供扩容决策依据

### 扩容策略
- **基础容量**: 3 个常驻 Node（minReplicaCount）
- **扩容逻辑**: running pods = active sessions + 2
- **最大容量**: 100 个 Node（maxReplicaCount）
- **扩容间隔**: 5 秒轮询，180 秒冷却期

## 📋 前置要求

### 系统要求
- Kubernetes 集群（1.20+）
- kubectl 命令行工具
- Helm 3.0+
- 节点可拉取镜像 `chrome-tinyproxy-node:latest`

### 网络要求
- 集群内服务通信正常
- 节点可访问外部网络（用于代理功能）
- 端口 30444 对外可访问（Hub Web UI）

## 🚀 快速部署

### 一键部署（推荐）
```bash
cd mini/docker/k8s
./quick-deploy.sh
```

### 分步部署
```bash
# 1. 部署 Selenium Grid
./deploy.sh

# 2. 安装 KEDA
./install-keda.sh

# 3. 应用扩容配置
kubectl apply -f keda-metricsapi-scaledobject.yaml
```

## 🔧 配置说明

### 端口映射
| 服务 | 端口 | 说明 |
|------|------|------|
| Hub Web UI | 30444 | 对外访问端口 |
| Hub GraphQL | 30444/graphql | API 接口 |
| Event Bus | 30442, 30443 | 内部通信 |
| VNC | 5900 | 远程桌面（需 port-forward） |
| noVNC | 7900 | Web VNC（需 port-forward） |

### 资源配置
| 组件 | CPU 请求/限制 | 内存请求/限制 | 共享内存 |
|------|----------------|----------------|----------|
| Chrome Node | 500m / 2 | 1536Mi / 2Gi | 2Gi |
| Hub | 500m / 1 | 512Mi / 1Gi | - |
| 指标导出器 | 100m / 500m | 128Mi / 256Mi | - |

### 存储配置
- **Chrome 用户数据**: 使用 emptyDir，限制 1Gi
- **共享内存**: 使用 Memory 类型 emptyDir，限制 2Gi
- **会话数据**: 容器重启后丢失，适合无状态部署

## 📊 监控和扩容

### 查看扩容状态
```bash
# 查看 ScaledObject 状态
kubectl -n selenium-grid get scaledobject

# 查看 HPA 状态
kubectl -n selenium-grid get hpa

# 查看 Pod 数量和状态
kubectl -n selenium-grid get pods -l app=chrome-node
```

### 扩容测试
```bash
# 运行并发测试脚本
python3 test_scaling.py

# 手动创建测试会话
python3 -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
driver = webdriver.Remote('http://172.16.1.129:30444/wd/hub', options=options)
driver.get('http://httpbin.org/ip')
print('Session created successfully')
driver.quit()
"
```

### 实时监控
```bash
# 监控 Pod 状态变化
watch -n 5 'kubectl -n selenium-grid get pods'

# 监控扩容状态
watch -n 5 'kubectl -n selenium-grid get scaledobject'

# 监控资源使用
watch -n 5 'kubectl -n selenium-grid top pods'
```

### Kubernetes Dashboard

> Dashboard 清单位于 `docker/k8s/kubernetes-dashboard.yaml` 与 `docker/k8s/kubernetes-dashboard-admin.yaml`，默认部署在 `kubernetes-dashboard` 命名空间，镜像版本与清单保持一致（`kubernetesui/dashboard:v2.7.0`、`kubernetesui/metrics-scraper:v1.0.8`）。以下命令默认在 `docker/k8s` 目录执行，若在仓库根目录请补上相对路径。

1. **准备镜像**（离线或 kind 集群时可先拉取并导入）：
   ```bash
   docker pull kubernetesui/dashboard:v2.7.0
   docker pull kubernetesui/metrics-scraper:v1.0.8

   # kind 集群名可以通过 `kind get clusters` 查看
   kind load docker-image kubernetesui/dashboard:v2.7.0 --name selenium-cluster
   kind load docker-image kubernetesui/metrics-scraper:v1.0.8 --name selenium-cluster
   ```
2. **部署组件**：
   ```bash
   kubectl apply -f kubernetes-dashboard.yaml
   ```
3. **创建登录账号**（可按需调整权限）：
   ```bash
   kubectl apply -f kubernetes-dashboard-admin.yaml
   # 生成登录用 token
   kubectl -n kubernetes-dashboard create token dashboard-admin
   ```
4. **访问方式**：
   ```bash
   # 在集群节点或通过 SSH 端口转发保持运行
   kubectl proxy --address=127.0.0.1 --port=8001
   ```
   - 本地浏览器访问 `http://127.0.0.1:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/`
   - 选择 **Token** 登录，粘贴上一步生成的令牌
   - 记得在 Dashboard 左上角切换到业务命名空间（如 `selenium-grid` 或选择 All namespaces）

5. **常见问题**：
   - Dashboard Pod CrashLoopBackOff：检查镜像是否已导入/可拉取，或使用 `kubectl describe pod -n kubernetes-dashboard kubernetes-dashboard-<suffix>` 查看原因
   - 浏览器无法直接访问服务器 `127.0.0.1:8001`：使用 SSH 隧道 `ssh -L 8001:127.0.0.1:8001 <user>@<server-ip>` 后再访问本地地址

6. **卸载**：
   ```bash
   kubectl delete -f kubernetes-dashboard-admin.yaml
   kubectl delete -f kubernetes-dashboard.yaml
   ```

## 🧹 环境管理

### 清理环境
```bash
# 清理所有资源
./cleanup.sh

# 清理特定资源
kubectl -n selenium-grid delete all --all
kubectl -n selenium-grid delete scaledobject --all
kubectl delete namespace selenium-grid
```

### 更新配置
```bash
# 更新部署配置
kubectl apply -f node-deployment.yaml

# 重启部署
kubectl -n selenium-grid rollout restart deployment/chrome-node

# 查看更新状态
kubectl -n selenium-grid rollout status deployment/chrome-node
```

### 版本回滚
```bash
# 查看部署历史
kubectl -n selenium-grid rollout history deployment/chrome-node

# 回滚到指定版本
kubectl -n selenium-grid rollout undo deployment/chrome-node --to-revision=2
```

## 🔍 故障排查

### 常见问题

#### 1. Pod 启动失败
```bash
# 查看 Pod 详细信息
kubectl -n selenium-grid describe pod <pod-name>

# 查看 Pod 事件
kubectl -n selenium-grid get events --sort-by='.lastTimestamp'
```

#### 2. 扩容不工作
```bash
# 检查 KEDA 状态
kubectl -n keda get pods

# 检查指标导出器
kubectl -n selenium-grid logs deploy/grid-metrics-exporter

# 测试指标接口
kubectl -n selenium-grid port-forward svc/grid-metrics-exporter 8080:8080
curl http://localhost:8080/value
```

#### 3. 连接问题
```bash
# 测试服务连通性
kubectl -n selenium-grid run test-curl --image=busybox --rm -it --restart=Never -- wget -O- http://selenium-hub:4444

# 检查 DNS 解析
kubectl -n selenium-grid run test-dns --image=busybox --rm -it --restart=Never -- nslookup selenium-hub
```

### 日志查看
```bash
# 查看 Hub 日志
kubectl -n selenium-grid logs -f deploy/selenium-hub

# 查看 Chrome Node 日志
kubectl -n selenium-grid logs -f deploy/chrome-node

# 查看指标导出器日志
kubectl -n selenium-grid logs -f deploy/grid-metrics-exporter

# 查看 KEDA 日志
kubectl -n keda logs -f deployment/keda-operator
```

## 📚 运维维护

### 日常维护
- 定期检查 Pod 状态和资源使用
- 监控扩容性能和响应时间
- 清理失败的 Pod 和 Job
- 备份重要配置文件

### 性能调优
- 根据实际负载调整资源限制
- 优化扩容参数（轮询间隔、冷却期）
- 调整会话超时和并发数
- 监控网络和存储性能

### 备份恢复
```bash
# 备份配置
kubectl -n selenium-grid get all -o yaml > selenium-grid-backup-$(date +%Y%m%d).yaml

# 恢复配置
kubectl apply -f selenium-grid-backup-YYYYMMDD.yaml
```

## 📁 文件结构

```
mini/docker/k8s/
├── README.md                    # 本文件 - 运维部署指南
├── MAINTENANCE.md              # 运维维护指南
├── quick-deploy.sh             # 一键部署脚本
├── deploy.sh                   # Selenium Grid 部署脚本
├── install-keda.sh             # KEDA 安装脚本
├── cleanup.sh                  # 环境清理脚本
├── test_scaling.py             # 扩容测试脚本
├── namespace.yaml              # 命名空间配置
├── hub-deployment.yaml         # Hub 部署配置
├── hub-service.yaml            # Hub 服务配置
├── node-deployment.yaml        # Chrome Node 部署配置
├── grid-metrics-exporter.yaml  # 指标导出器部署
├── grid-metrics-exporter-configmap.yaml  # 指标导出器配置
├── keda-metricsapi-scaledobject.yaml     # KEDA 扩容配置
├── keda-values.yaml            # KEDA Helm 配置
└── kind-config.yaml            # Kind 集群配置（开发环境）
```

## 🎯 快速命令参考

### 状态检查
```bash
kubectl -n selenium-grid get all                    # 查看所有资源
kubectl -n selenium-grid get pods -o wide           # 查看 Pod 状态
kubectl -n selenium-grid get svc -o wide            # 查看服务状态
kubectl -n selenium-grid get scaledobject           # 查看扩容配置
```

### 日志查看
```bash
kubectl -n selenium-grid logs -f deploy/selenium-hub      # Hub 日志
kubectl -n selenium-grid logs -f deploy/chrome-node       # Node 日志
kubectl -n selenium-grid logs -f deploy/grid-metrics-exporter  # 指标日志
```

### 扩容管理
```bash
kubectl -n selenium-grid scale deployment chrome-node --replicas=5  # 手动扩容
kubectl -n selenium-grid edit scaledobject chrome-node-autoscale-metrics  # 编辑扩容配置
```

### 故障处理
```bash
kubectl -n selenium-grid delete pods --field-selector=status.phase=Failed  # 清理失败 Pod
kubectl -n selenium-grid rollout restart deployment/chrome-node            # 重启部署
kubectl -n selenium-grid rollout undo deployment/chrome-node --to-revision=2  # 版本回滚
```

## 📞 技术支持

- **运维团队**: 运维团队联系方式
- **技术支持**: 技术支持联系方式
- **紧急联系**: 紧急情况联系方式

---

*最后更新时间: 2024年12月*
*维护团队: 运维团队*
