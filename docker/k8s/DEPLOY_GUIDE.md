# Kubernetes 部署速查手册

面向运维的快速部署步骤，覆盖先决条件、镜像准备、部署、验证以及常见问题。

## 1. 先决条件
- Kubernetes 1.24+ 集群（prod 环境建议准备 3+ 节点，确保 NAS/网络权限）。
- 工具链：`kubectl`、`helm 3`、`docker`，如使用 kind 需安装 `kind`。
- 镜像可拉取或提前导入节点（Selenium Hub、chrome 节点、自定义 exporter、Jaeger、kube-prometheus-stack、loki-stack、KEDA）。
- 阿里云 NAS：提前开通并在 `chrome-nas-*.yaml` 中调整 `server/path`。

## 2. 仓库准备
```bash
git clone <repo>
cd mini/docker/k8s
```
如需调整参数：
- `hub-deployment.yaml`：线程池、超时、NodePort。
- `node-deployment.yaml`：副本数、资源、代理、NAS PVC 名。
- `selenium-observability-configmap.yaml`：日志/Tracing 级别。
- `grid-metrics-exporter-configmap.yaml`：BUFFER 等采集参数。

## 3. 镜像导入（离线/kind 场景）
```bash
docker pull selenium/hub:latest
# ... 其他镜像
kind load docker-image selenium/hub:latest --name selenium-cluster
```
确保 KEDA 镜像 (`ghcr.io/kedacore/...`) 也已注入，否则会创建 `kedaorg-certs` 失败导致扩容不可用。

## 4. 一键部署
执行 `./deploy.sh` 即可自动完成：
1. 创建命名空间、NAS PV/PVC
2. 部署 Hub、Node、Exporter
3. 安装 kube-prometheus-stack、Loki、Jaeger、OpenTelemetry Collector
4. 安装 KEDA + ScaledObject

常用参数：
| 选项 | 说明 |
|------|------|
| `--cleanup-first` | 部署前执行 `cleanup.sh --skip-kind-delete` |
| `--skip-image-load` | 跳过脚本内的镜像导入 |
| `--load-image repo/image:tag` | 额外导入自定义镜像 |
| `--port-forward` | 部署完成后自动开 Grafana/Prometheus port-forward |
| `--expose-nodeport` | 使用 iptables 将 NodePort 映射到宿主机 30080/30090 |

若需要分步部署，可参考 README 中的 4.2 节。

## 5. 验证
- **检查 Pod**：
  ```bash
  kubectl -n selenium-grid get pods
  kubectl -n monitoring get pods
  ```
- **Grafana**：
  ```bash
  kubectl -n monitoring port-forward svc/monitoring-grafana 30080:80
  # 浏览器访问 http://127.0.0.1:30080  用户：admin / prom-operator
  ```
  看板：Dashboards → Selenium → Selenium Grid Overview。
- **Prometheus**：`kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 30090:9090`
  - 常用查询：`selenium_grid_sessions_active`、`selenium_session_queue_size`。
- **Jaeger**：`kubectl -n monitoring port-forward svc/jaeger-query 16686:16686`
  - 浏览器访问 `http://127.0.0.1:16686` 检查 `selenium-hub` trace。
- **日志**：Grafana → Explore → Loki 数据源，查询 `{namespace="selenium-grid"}`。

## 6. 常见问题
| 问题 | 排查 |
|------|------|
| Hub 无法连接 | `kubectl -n selenium-grid logs deploy/selenium-hub`，检查 `SE_HUB_HOST`/Service | 
| Session 排队 | Grafana 看板 `Session Queue Size`，PromQL `selenium_session_queue_size` | 
| KEDA 不扩容 | `kubectl -n keda get pods`；查看 `grid-metrics-exporter` 是否返回 200；检查 `ScaledObject` 状态 | 
| NAS 挂载失败 | 查看 Pod Event，确认 NAS `server/path` 和权限；必要时改用本地 `emptyDir` 测试 | 
| Trace/日志缺失 | `kubectl -n monitoring logs deploy/otel-collector`、`kubectl -n monitoring get pods -l app=jaeger` | 

## 7. 扩缩容与维护
- **手动扩容**：`kubectl -n selenium-grid scale deployment chrome-node --replicas=20`
- **调整线程池**：修改 `hub-deployment.yaml` 中 `SE_NEW_SESSION_THREAD_POOL_SIZE` 并 `kubectl rollout restart deploy/selenium-hub`
- **压测脚本**：
  ```bash
  python docker/k8s/test_scaling.py --concurrency 50 --keep-alive 60
  ```
  输出会显示每个会话的连接耗时及平均值。
- **清理**：`./cleanup.sh --skip-kind-delete` 或 `./cleanup.sh --delete-kind`

## 8. 版本记录
- 2025-09：新增 `selenium_session_queue_size` 指标、Jaeger 替换 Tempo、Grafana 看板同步更新、压测脚本增强。

