# Selenium Grid on Kubernetes 部署与运维指南

本指南覆盖 SpotLight Selenium Grid 集群的最新部署方式、自动扩缩容机制以及日常维护要点，已同步近期对 KEDA、指标导出器和脚本所做的更新。

## 1. 架构与扩缩容概览

### 1.1 核心组件
- **Selenium Hub** (`hub-deployment.yaml`, `hub-service.yaml`): 统一调度 WebDriver 会话，并通过 NodePort 暴露 30444 Web UI/GraphQL。
- **Chrome Node** (`node-deployment.yaml`): 每个 Pod 内含浏览器容器 + tinyproxy sidecar，支持 VNC/noVNC 调试，并挂载 NAS 用户数据目录。
- **Grid Metrics Exporter** (`grid-metrics-exporter*.yaml`): 轮询 Hub GraphQL，输出当前活跃会话数给自动扩缩容逻辑。
- **KEDA**: 运行在 `keda` 命名空间的自动扩缩容控制器，基于自定义指标动态调整 `chrome-node` 副本数。
- **持久化存储** (`chrome-nas-*.yaml`): 通过阿里云 NAS (RWX) 保存 Chrome 用户数据，保证多 Pod 共享会话目录。

### 1.2 自动扩缩容策略
- **指标来源**: `grid-metrics-exporter` 暴露 `GET /value`，返回 `value = max(active_sessions + BUFFER, BUFFER)`；默认 `BUFFER=2`（可通过环境变量修改）。
- **KEDA 触发器**: `keda-metricsapi-scaledobject.yaml` 使用 `metrics-api` 类型，`targetValue=1` 表示直接以返回值作为期望副本数。
- **关键参数**:
  - `minReplicaCount = 8`：常驻 8 个 Chrome Node，减轻冷启动等待。
  - `maxReplicaCount = 100`：上限 100。
  - `pollingInterval = 2s`，`cooldownPeriod = 30s`：快速响应峰值，并在会话回落后 30 秒内收缩。
  - `SE_NODE_MAX_SESSIONS = 1`（如需每 Pod 多会话，注意同步调整指标计算公式）。

## 2. 先决条件
- Kubernetes 1.20+ 集群，可使用 kind (`kind-config.yaml` 提供单节点配置)。
- 工具链：`kubectl`, `docker`, `helm 3`, 可选 `kind`。
- 已构建或可拉取以下镜像：
  - `chrome-tinyproxy-node:latest`
  - `selenium/hub:latest`
  - `python:3.11-slim`（指标导出器）
  - `ghcr.io/kedacore/keda:2.17.2`
  - `ghcr.io/kedacore/keda-admission-webhooks:2.17.2`
  - `ghcr.io/kedacore/keda-metrics-apiserver:2.17.2`
- 集群节点需可访问阿里云 NAS（或按需调整 PV/PVC 配置）。

## 3. 镜像准备
在离线或 kind 场景下，先拉取镜像并注入集群节点：
```bash
# 拉取业务镜像
docker build -t chrome-tinyproxy-node:latest ../..   # 如已构建可跳过

docker pull selenium/hub:latest
docker pull python:3.11-slim

docker pull ghcr.io/kedacore/keda:2.17.2
docker pull ghcr.io/kedacore/keda-admission-webhooks:2.17.2
docker pull ghcr.io/kedacore/keda-metrics-apiserver:2.17.2

# 注入 kind 集群（集群名示例：selenium-cluster）
kind load docker-image chrome-tinyproxy-node:latest --name selenium-cluster
kind load docker-image selenium/hub:latest --name selenium-cluster
kind load docker-image python:3.11-slim --name selenium-cluster
kind load docker-image ghcr.io/kedacore/keda:2.17.2 --name selenium-cluster
kind load docker-image ghcr.io/kedacore/keda-admission-webhooks:2.17.2 --name selenium-cluster
kind load docker-image ghcr.io/kedacore/keda-metrics-apiserver:2.17.2 --name selenium-cluster
```
> **若不注入 KEDA 镜像**，在受限网络环境中会出现 `ImagePullBackOff`，并导致 `kedaorg-certs` Secret 无法生成，自动扩容会失效。

## 4. 部署流程

### 4.1 脚本模式

`deploy.sh` 现已内置常见参数，可按需选择：

| 场景 | 命令 |
|------|------|
| 首次部署（自动加载本地镜像） | `./deploy.sh` |
| 在原集群上重新部署 | `./deploy.sh --cleanup-first` |
| 已手动执行 `kind load`，跳过脚本导入 | `./deploy.sh --skip-image-load` |
| 额外导入自定义镜像 | `./deploy.sh --load-image myrepo/custom:tag` |
| 部署后自动开启本地 `port-forward`（推荐开发机） | `./deploy.sh --port-forward` |
| 将 NodePort 映射到宿主机固定端口（需 root） | `./deploy.sh --expose-nodeport` |

`--cleanup-first` 会调用 `cleanup.sh --skip-kind-delete` 先清理命名空间等资源，但保留 kind 集群；若未检测到集群则自动跳过。

### 4.2 分步部署
1. **创建或连接集群**（kind 或自建集群）。
2. **创建命名空间与存储**：
   ```bash
   kubectl apply -f namespace.yaml
   kubectl apply -f chrome-nas-storageclass.yaml
   kubectl apply -f chrome-nas-pv.yaml
   kubectl apply -f chrome-nas-pvc.yaml
   ```
3. **部署 Selenium Hub / Node / 指标导出器**：
   ```bash
   kubectl apply -f hub-deployment.yaml -f hub-service.yaml
   kubectl apply -f node-deployment.yaml
   kubectl apply -f grid-metrics-exporter-configmap.yaml
   kubectl apply -f grid-metrics-exporter.yaml
   ```
4. **安装或修复 KEDA**：
   - 推荐脚本：`./install-keda.sh`（封装 `helm upgrade --install`，会自动创建 `keda` 命名空间并开启 metrics server）。
   - `deploy.sh` 同样包含 Helm 安装逻辑，若已运行可跳过本步骤。
5. **应用 ScaledObject**：
   ```bash
   kubectl apply -f keda-metricsapi-scaledobject.yaml
   ```
6. **检查状态**：
   ```bash
   kubectl -n selenium-grid get pods
   kubectl -n keda get pods
   kubectl -n selenium-grid describe scaledobject chrome-node-autoscale-metrics
   ```
   `ScaledObject` 状态需显示 `Ready=True` / `Active=True`。

## 5. 配置要点

### 5.1 Selenium Hub
- 默认 NodePort 30444；可在 `hub-service.yaml` 中修改。
- `SE_NEW_SESSION_THREAD_POOL_SIZE=200` 等参数已在 `hub-deployment.yaml` 调优。

### 5.2 Chrome Node
- 资源请求：`cpu 500m/limit 1000m`, `memory 500Mi/limit 1Gi`，共享内存 `emptyDir` 512Mi。
- Sidecar `tinyproxy` 默认 root 运行，监听 3128；主容器通过环境变量 `HTTP_PROXY/HTTPS_PROXY` 指向 sidecar。
- 每个 Pod 默认仅处理 1 个会话（`SE_NODE_MAX_SESSIONS=1`）。

### 5.3 NAS 存储
- StorageClass 使用 `nas.csi.aliyun.com`，请根据实际环境调整 `server/path`。
- Pod 挂载点 `/opt/chrome_user_data`，支持多 Pod 共享用户目录。

### 5.4 指标导出器
- 通过 ConfigMap 部署脚本，`BUFFER` 默认 2，可在 `grid-metrics-exporter.yaml` 中覆盖。
- 若 Hub GraphQL 不可达，接口会返回 500，KEDA 会回落到 `minReplicaCount`。

### 5.5 KEDA ScaledObject
- 对象名：`chrome-node-autoscale-metrics`。
- 关联 HPA：`keda-hpa-chrome-node-autoscale-metrics`。
- 修改扩缩容逻辑时请同步更新 `BUFFER`、`targetValue` 以及 `node-deployment.yaml` 中的并发设置。

## 6. 观测体系概览

本项目的观测链路由三部分组成：

| 能力 | 组件 | 说明 |
|------|------|------|
| 指标 Metrics | kube-prometheus-stack（Prometheus + Alertmanager + Grafana）<br/>自研 `grid-metrics-exporter` | 采集 Kubernetes 及 Selenium Grid 指标，Grafana 内置 *Selenium Grid Overview* 看板；Exporter 负责补全 Hub/Node 指标。 |
| 日志 Logs | Loki + Promtail | Selenium Hub/Node 输出结构化 JSON 日志，通过 Loki Stack 收集，可在 Grafana Explore 中查询。 |
| 链路 Traces | OpenTelemetry Collector + Jaeger all-in-one | Selenium Hub/Node 通过 OTLP 将 Span 发给 Collector，再转发至 Jaeger，提供可视化及分析能力。 |

### 6.1 部署/访问监控栈

部署脚本 `deploy.sh` 会自动安装/升级以下组件：

1. **kube-prometheus-stack**：Prometheus、Grafana、kube-state-metrics 等基座。
2. **Loki Stack**：日志采集与存储。
3. **OpenTelemetry Collector**：统一接收 Selenium OTLP 数据。
4. **Jaeger all-in-one**：链路查询 UI 与存储。

若需手动安装 kube-prometheus-stack，可参考：

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.service.type=NodePort \
  --set grafana.service.nodePort=32000 \
  --set prometheus.service.type=NodePort \
  --set prometheus.service.nodePort=32001
```

Grafana 初始密码：

```bash
kubectl -n monitoring get secret monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
```

### 6.2 访问入口

部署脚本提供两种访问方式，可按实际环境选择其一或同时启用：

1. **Port-forward（方便开发机/远程 IDE）**
   - 执行 `./deploy.sh --port-forward` 或单独运行：
     ```bash
     kubectl -n monitoring port-forward --address 0.0.0.0 svc/monitoring-grafana 30080:80
     kubectl -n monitoring port-forward --address 0.0.0.0 svc/monitoring-kube-prometheus-prometheus 30090:9090
     ```
   - 在 Cursor / VS Code 端口转发面板添加 30080、30090，即可在本机访问 `http://127.0.0.1:30080`（Grafana，默认密码 `prom-operator`）和 `http://127.0.0.1:30090`（Prometheus）。
   - 停止方法：`pkill -f 'monitoring port-forward'` 或结束具体 PID，日志位于 `/tmp/grafana-port-forward.log`、`/tmp/prometheus-port-forward.log`。

2. **宿主机端口映射（生产/长期使用）**
   - 执行 `./deploy.sh --expose-nodeport`，脚本会使用 `iptables` 将 NodePort 32000/32001 重定向到宿主机 30080/30090。
   - 需具备 `sudo` 权限，并确保云主机安全组/防火墙放行 30080、30090 端口。
   - 外部直接访问 `http://<宿主机IP>:30080` / `:30090`。
   - 想清除映射，可执行：
     ```bash
     sudo iptables -t nat -D PREROUTING -p tcp --dport 30080 -j REDIRECT --to-port 32000
     sudo iptables -t nat -D OUTPUT -p tcp --dport 30080 -j REDIRECT --to-port 32000
     sudo iptables -t nat -D PREROUTING -p tcp --dport 30090 -j REDIRECT --to-port 32001
     sudo iptables -t nat -D OUTPUT -p tcp --dport 30090 -j REDIRECT --to-port 32001
     ```

### 6.3 Selenium Logging & Tracing 配置

- **日志格式**：Hub 与 Chrome Node 已根据 `selenium-observability-configmap.yaml` 启用结构化 JSON 日志 (`SE_STRUCTURED_LOGS=true`) 与 HTTP 请求日志 (`SE_HTTP_LOGS=true`)。
  ```bash
  kubectl -n selenium-grid logs deploy/selenium-hub | jq .
  kubectl -n selenium-grid logs deploy/chrome-node | jq '.message'
  ```
  可在 ConfigMap 中调整 `SE_LOG_LEVEL`、`SE_STRUCTURED_LOGS`/`SE_HTTP_LOGS` 等参数并重新部署。

- **Tracing 管道**：`otel-collector.yaml` 在 `monitoring` 命名空间部署 OpenTelemetry Collector，接收 Hub/Node 发送的 OTLP spans。
  - Collector 默认同时导出到 `logging`（排查时可看 Collector Pod 日志）与 Jaeger (`jaeger-collector.monitoring.svc:4317`)。
  - 访问 Jaeger UI：`kubectl -n monitoring port-forward svc/jaeger-query 16686:16686`，浏览器打开 `http://127.0.0.1:16686` 即可按 `service.name`、`operation` 等条件检索链路；如需公网访问，可为 `jaeger-query` 配置 NodePort/Ingress。
  - 若要对接外部链路平台，编辑 `otel-collector-config` 中的 `exporters`（例如新增 `otlphttp` 指向 SaaS），更新后执行 `kubectl apply -f otel-collector.yaml` 并滚动重启 `otel-collector`。
  - Selenium 侧的 OTLP 目标通过 `SE_OTEL_EXPORTER_ENDPOINT=http://otel-collector.monitoring.svc.cluster.local:4317` 统一指向 Collector，便于在 Collector 层做多路导出。

- **Prometheus 指标**：启用 tracing 后仍会输出 Prometheus metrics，可在 Grafana 中创建面板展示 `selenium_grid_active_sessions`（来自 grid-metrics-exporter 扩展）或 `otelcol_receiver_accepted_spans_total` 等 collector 指标，用于监测链路健康。

### 6.4 指标监控（Prometheus + Grafana）

- **内置看板**：部署后自动创建 ConfigMap `selenium-grid-dashboard`，Grafana 会出现 *Dashboards → Selenium → Selenium Grid Overview*，涵盖活跃会话、节点可用率、槽位利用率、浏览器分布、单节点容量等核心图表。
- **自定义查询**：在 Grafana Explore 或 Prometheus Web UI 中，可使用下列 PromQL 进行排查：
  * `selenium_grid_sessions_active`：当前活跃会话数。
  * `sum by (browser) (selenium_grid_browser_sessions)`：各浏览器会话占比。
  * `selenium_grid_node_sessions / selenium_grid_node_slots`：各节点槽位利用率。
  * `rate(selenium_grid_scrape_error_info[5m]) > 0`：Exporter 抓取异常告警。
- **Exporter 验证**：
  ```bash
  kubectl -n selenium-grid port-forward svc/grid-metrics-exporter 18080:8080
  curl -s http://127.0.0.1:18080/metrics | head
  ```
  若 Prometheus 未采集到 `selenium_grid_*` 指标，请检查 `selenium-monitoring.yaml` 中 `ServiceMonitor` 标签与 Prometheus 选择器是否匹配。

### 6.5 日志检索（Loki + Grafana）

- **数据源**：部署脚本安装 loki-stack，并在 Grafana 中自动注册 Loki 数据源。
- **查询示例**：Grafana → Explore → 选择 Loki → 输入 `{namespace="selenium-grid", app="selenium-hub"}` 查看 Hub 日志；可用 `| json` 解析结构化字段，例如 `| json | line_format "{{.message}} session={{.attributes.session.id}}"`。
- **日志级别**：可在 `selenium-observability-configmap.yaml` 调整 `SE_LOG_LEVEL`、`SE_STRUCTURED_LOGS`、`SE_HTTP_LOGS` 等参数并滚动重启 Deployment。
- **问题定位**：若日志缺失，确认 `loki-promtail-*` Pod 状态，或检查 `kubectl -n monitoring logs -l app=loki` 是否有存储/权限异常。

### 6.6 链路追踪（Jaeger）

- **Collector 管道**：Selenium Hub/Node 设置 `SE_OTEL_EXPORTER_ENDPOINT=http://otel-collector.monitoring.svc.cluster.local:4317`，Collector (`otel-collector.yaml`) 将 Span 同时输出到日志与 `jaeger-collector`。
- **验证链路**：
  ```bash
  kubectl -n monitoring port-forward svc/jaeger-query 16686:16686
  curl -s http://127.0.0.1:16686/api/services
  ```
  出现 `selenium-node-chrome`/`selenium-hub` 说明数据写入 Jaeger 成功。
- **UI 操作**：浏览器打开 `http://127.0.0.1:16686`，按 `service.name`、`operation`、标签等筛选；可结合 *Trace Timeline* 查看 Hub → Node 整体耗时。若需长期保存，可改用 Jaeger Operator 并配置存储后端（Elasticsearch、ClickHouse 等）。
- **Collector 故障排查**：查看 `kubectl -n monitoring logs deploy/otel-collector`，若存在 `connection refused`，确认 `jaeger-collector` 服务与端口是否可达，或在 Collector 中添加 `debug` 导出器调试。

### 6.7 快速健康检查

- **扩缩容状态**：`kubectl -n selenium-grid get scaledobject`, `kubectl -n selenium-grid get hpa`
- **资源监控**：`watch -n 5 'kubectl -n selenium-grid top pods'`
- **指标接口**：
  ```bash
  kubectl -n selenium-grid port-forward svc/grid-metrics-exporter 18080:8080
  curl http://127.0.0.1:18080/value
  ```
- **并发压测**：`python test_scaling.py`（Barrier 并发，验证 KEDA 伸缩速度）

## 7. 常用运维操作

| 操作 | 命令 |
|------|------|
| 查看资源 | `kubectl -n selenium-grid get all` |
| 查看日志 | `kubectl -n selenium-grid logs -f deploy/selenium-hub` |
| 手动扩容 | `kubectl -n selenium-grid scale deployment chrome-node --replicas=12` |
| 修改扩容规则 | `kubectl -n selenium-grid edit scaledobject chrome-node-autoscale-metrics` |
| 重启节点 | `kubectl -n selenium-grid rollout restart deployment/chrome-node` |
| 清理环境（保留 kind 集群） | `./cleanup.sh --skip-kind-delete` |
| 完全清理并删除 kind 集群 | `./cleanup.sh --delete-kind` |
| 停止全部 port-forward | `pkill -f 'monitoring port-forward'` |
| 重置 NodePort 映射 | 参考上文 iptables 清理命令 |
| 查看 Collector traces | `kubectl -n monitoring logs deploy/otel-collector` |
| 调整日志/追踪配置 | `kubectl -n selenium-grid edit configmap selenium-observability` |
| 打开 Jaeger UI | `kubectl -n monitoring port-forward svc/jaeger-query 16686:16686` 后访问 `http://127.0.0.1:16686` |

## 8. 故障排查

| 问题 | 现象 | 处理建议 |
|------|------|----------|
| KEDA `ImagePullBackOff` | `kubectl -n keda get pods` 显示拉取失败 | 预先 `docker pull` 并 `kind load` 对应镜像，或保证节点可访问 ghcr.io；删除旧 Pod 以重新创建 `kedaorg-certs`。 |
| ScaledObject 未生效 | `describe scaledobject` 显示非 Ready | 确认 KEDA Pod 运行且指标服务返回 200；查看 `kubectl -n keda logs deploy/keda-operator`。 |
| Chrome Node 不扩容 | 指标接口返回固定值 | 排查 `grid-metrics-exporter` 日志/端口转发；确认 Hub GraphQL `/graphql` 可访问。 |
| NAS 挂载失败 | Pod Event 显示 `volume mount` 错误 | 检查 NAS 地址、权限、SecurityGroup；必要时使用本地 PV 做替代测试。 |

## 9. 文件结构速览
```
mini/docker/k8s/
├── README.md                     # 本指南
├── MAINTENANCE.md                # 维护任务详解
├── deploy.sh                     # 自动部署脚本（支持清理/镜像参数）
├── install-keda.sh               # KEDA 安装脚本
├── cleanup.sh                    # 清理脚本
├── namespace.yaml                # 命名空间
├── hub-*.yaml                    # Hub 部署与服务
├── node-deployment.yaml          # Chrome Node 部署
├── chrome-nas-*.yaml             # NAS 存储定义
├── grid-metrics-exporter*.yaml   # 指标导出器
├── keda-metricsapi-scaledobject.yaml # KEDA 扩缩容配置
├── selenium-observability-configmap.yaml # Selenium Logging/Tracing 配置
├── otel-collector.yaml           # OpenTelemetry Collector 部署
├── jaeger.yaml                   # Jaeger all-in-one 部署
├── test_scaling.py               # 扩容压测脚本
└── kind-config.yaml              # kind 集群示例配置
```

## 10. 版本信息
- 文档版本：2025-09
- 维护者：SpotLight 运维与测试平台团队

> 有任何问题或改进建议，可通过团队沟通渠道或提交 PR 反馈。
