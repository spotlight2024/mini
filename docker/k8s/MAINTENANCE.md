# Selenium Grid 运维维护指南

## 📋 目录
- [日常维护](#日常维护)
- [故障排查](#故障排查)
- [监控指标](#监控指标)
- [扩容调优](#扩容调优)
- [备份恢复](#备份恢复)

## 🔧 日常维护

### 1. 状态检查
```bash
# 检查所有资源状态
kubectl -n selenium-grid get all

# 检查 Pod 状态
kubectl -n selenium-grid get pods -o wide

# 检查服务状态
kubectl -n selenium-grid get svc -o wide

# 检查扩容配置
kubectl -n selenium-grid get scaledobject
```

### 2. 日志查看
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

### 3. 资源清理
```bash
# 清理失败的 Pod
kubectl -n selenium-grid delete pods --field-selector=status.phase=Failed

# 清理已完成的 Job
kubectl -n selenium-grid delete jobs --field-selector=status.successful=1
```

## 🚨 故障排查

### 1. Pod 启动失败
```bash
# 查看 Pod 详细信息
kubectl -n selenium-grid describe pod <pod-name>

# 查看 Pod 事件
kubectl -n selenium-grid get events --sort-by='.lastTimestamp'

# 查看容器日志
kubectl -n selenium-grid logs <pod-name> -c chrome-node
```

### 2. 扩容不工作
```bash
# 检查 KEDA 状态
kubectl -n keda get pods
kubectl -n keda logs deployment/keda-operator

# 检查指标导出器
kubectl -n selenium-grid logs deploy/grid-metrics-exporter

# 测试指标接口
kubectl -n selenium-grid port-forward svc/grid-metrics-exporter 8080:8080
curl http://localhost:8080/value
```

### 3. 连接问题
```bash
# 检查网络策略
kubectl -n selenium-grid get networkpolicy

# 测试服务连通性
kubectl -n selenium-grid run test-curl --image=busybox --rm -it --restart=Never -- wget -O- http://selenium-hub:4444

# 检查 DNS 解析
kubectl -n selenium-grid run test-dns --image=busybox --rm -it --restart=Never -- nslookup selenium-hub
```

## 📊 监控指标

### 1. 关键指标
- **活跃会话数**: `kubectl -n selenium-grid get scaledobject -o jsonpath='{.items[0].status.scaleTargetRef.currentReplicas}'`
- **Pod 数量**: `kubectl -n selenium-grid get pods --no-headers | wc -l`
- **资源使用**: `kubectl -n selenium-grid top pods`

### 2. 性能监控
```bash
# 监控资源使用
watch -n 5 'kubectl -n selenium-grid top pods'

# 监控 Pod 状态
watch -n 5 'kubectl -n selenium-grid get pods'

# 监控扩容状态
watch -n 5 'kubectl -n selenium-grid get scaledobject'
```

### 3. 日志监控
```bash
# 实时监控错误日志
kubectl -n selenium-grid logs -f deploy/selenium-hub | grep -i error

# 监控会话创建日志
kubectl -n selenium-grid logs -f deploy/selenium-hub | grep -i "session.*created"
```

## ⚡ 扩容调优

### 1. 扩容参数调整
```bash
# 编辑扩容配置
kubectl -n selenium-grid edit scaledobject chrome-node-autoscale-metrics

# 主要参数说明:
# - pollingInterval: 指标轮询间隔（秒）
# - cooldownPeriod: 冷却期（秒）
# - minReplicaCount: 最小副本数
# - maxReplicaCount: 最大副本数
```

### 2. 资源限制调整
```bash
# 编辑 Chrome Node 部署
kubectl -n selenium-grid edit deployment chrome-node

# 调整资源配置:
# - CPU 请求/限制
# - 内存请求/限制
# - 共享内存大小
```

### 3. 性能优化
```bash
# 增加并发会话数
kubectl -n selenium-grid set env deployment/chrome-node SE_NODE_MAX_SESSIONS=2

# 调整会话超时
kubectl -n selenium-grid set env deployment/chrome-node SE_NODE_SESSION_TIMEOUT=300

# 重启部署
kubectl -n selenium-grid rollout restart deployment/chrome-node
```

## 💾 备份恢复

### 1. 配置备份
```bash
# 备份所有配置
kubectl -n selenium-grid get all -o yaml > selenium-grid-backup-$(date +%Y%m%d).yaml

# 备份扩容配置
kubectl -n selenium-grid get scaledobject -o yaml > scaledobject-backup-$(date +%Y%m%d).yaml
```

### 2. 配置恢复
```bash
# 恢复配置
kubectl apply -f selenium-grid-backup-YYYYMMDD.yaml

# 恢复扩容配置
kubectl apply -f scaledobject-backup-YYYYMMDD.yaml
```

### 3. 版本回滚
```bash
# 查看部署历史
kubectl -n selenium-grid rollout history deployment/chrome-node

# 回滚到指定版本
kubectl -n selenium-grid rollout undo deployment/chrome-node --to-revision=2
```

## 🆘 紧急情况

### 1. 服务完全不可用
```bash
# 强制重启所有 Pod
kubectl -n selenium-grid delete pods --all

# 检查集群状态
kubectl get nodes
kubectl -n selenium-grid get events --sort-by='.lastTimestamp'
```

### 2. 扩容失控
```bash
# 暂停扩容
kubectl -n selenium-grid patch scaledobject chrome-node-autoscale-metrics -p '{"spec":{"triggers":[]}}'

# 手动设置副本数
kubectl -n selenium-grid scale deployment chrome-node --replicas=3
```

### 3. 资源耗尽
```bash
# 查看节点资源
kubectl top nodes

# 查看 Pod 资源使用
kubectl -n selenium-grid top pods

# 清理资源
kubectl -n selenium-grid delete pods --field-selector=status.phase=Failed
```

## 📞 联系信息

- **运维团队**: 运维团队联系方式
- **技术支持**: 技术支持联系方式
- **紧急联系**: 紧急情况联系方式

---

*最后更新时间: 2024年12月*



