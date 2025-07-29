# ADB 代理日志控制功能

## 概述

ADB代理服务现在支持通过环境变量 `ADB_PROXY_LOG_LEVEL` 来控制日志输出级别，可以根据需要调整日志详细程度，在调试和性能之间找到平衡。

## 支持的日志级别

| 级别 | 说明 | 性能影响 | 适用场景 |
|------|------|----------|----------|
| `DEBUG` | 最详细的日志，包含所有请求和响应数据 | 高 | 调试和开发阶段 |
| `INFO` | 一般信息日志，包含连接和基本操作 | 中 | 日常运行和监控 |
| `WARNING` | 只显示警告和错误 | 低 | 生产环境监控 |
| `ERROR` | 只显示错误信息 | 很低 | 错误排查 |
| `CRITICAL` | 只显示严重错误 | 很低 | 紧急情况 |
| `NONE` | 完全关闭日志输出 | 无 | 最高性能要求 |

## 使用方法

### 1. 通过环境变量设置

```bash
# 设置详细日志（调试模式）
export ADB_PROXY_LOG_LEVEL=DEBUG

# 设置一般日志（默认）
export ADB_PROXY_LOG_LEVEL=INFO

# 设置警告级别日志
export ADB_PROXY_LOG_LEVEL=WARNING

# 设置错误级别日志
export ADB_PROXY_LOG_LEVEL=ERROR

# 设置严重错误级别日志
export ADB_PROXY_LOG_LEVEL=CRITICAL

# 完全关闭日志（最高性能）
export ADB_PROXY_LOG_LEVEL=NONE
```

### 2. 在 Docker Compose 中使用

```yaml
version: '3.8'
services:
  chrome-driver:
    build:
      context: .
      dockerfile: Dockerfile.custom-selenium-chrome
    environment:
      # 设置日志级别
      - ADB_PROXY_LOG_LEVEL=INFO
```

### 3. 在 Docker 运行时设置

```bash
# 启动容器时设置日志级别
docker run -e ADB_PROXY_LOG_LEVEL=DEBUG custom-selenium-chrome:adb_1

# 或者使用 NONE 获得最高性能
docker run -e ADB_PROXY_LOG_LEVEL=NONE custom-selenium-chrome:adb_1
```

## 性能优化建议

### 生产环境
- 使用 `WARNING` 或 `ERROR` 级别
- 避免使用 `DEBUG` 级别，因为会记录大量数据

### 高性能场景
- 使用 `NONE` 级别完全关闭日志
- 适用于对性能要求极高的场景

### 调试阶段
- 使用 `DEBUG` 级别获取详细信息
- 开发完成后切换到 `INFO` 或 `WARNING`

## 示例配置

### 高性能模式
```yaml
environment:
  - ADB_PROXY_LOG_LEVEL=NONE
```

### 生产环境模式
```yaml
environment:
  - ADB_PROXY_LOG_LEVEL=WARNING
```

### 调试模式
```yaml
environment:
  - ADB_PROXY_LOG_LEVEL=DEBUG
```

## 日志输出示例

### DEBUG 级别
```
2025-07-29 09:01:42,123 [INFO] ADB 代理脚本开始启动
2025-07-29 09:01:42,124 [INFO] 代理监听地址: 0.0.0.0:5037
2025-07-29 09:01:42,125 [INFO] 目标ADB服务地址: 127.0.0.1:5038
2025-07-29 09:01:42,126 [INFO] 日志级别: DEBUG
2025-07-29 09:01:42,127 [INFO] 新连接: ('127.0.0.1', 12345)
2025-07-29 09:01:42,128 [INFO] 已连接到真实 adb 服务: 127.0.0.1:5038
2025-07-29 09:01:42,129 [INFO] C->S [('127.0.0.1', 12345)]
STR: host:transport:emulator-5554
2025-07-29 09:01:42,130 [INFO] S->C [('127.0.0.1', 12345)]
STR: OKAY
```

### NONE 级别
```
# 无日志输出，只有启动信息
2025-07-29 09:01:42,123 [INFO] ADB 代理脚本开始启动
2025-07-29 09:01:42,124 [INFO] 代理监听地址: 0.0.0.0:5037
2025-07-29 09:01:42,125 [INFO] 目标ADB服务地址: 127.0.0.1:5038
2025-07-29 09:01:42,126 [INFO] 日志级别: NONE
```

## 注意事项

1. **性能影响**：`DEBUG` 级别会显著影响性能，建议只在调试时使用
2. **存储空间**：详细日志会占用更多存储空间
3. **实时性**：日志输出是实时的，不会影响代理功能
4. **重启生效**：修改环境变量后需要重启容器才能生效

## 故障排除

### 如果日志级别设置无效
1. 检查环境变量名称是否正确：`ADB_PROXY_LOG_LEVEL`
2. 检查值是否为大写：`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, `NONE`
3. 重启容器确保环境变量生效

### 如果性能仍然不理想
1. 尝试使用 `NONE` 级别完全关闭日志
2. 检查是否有其他日志输出（如Selenium日志）
3. 考虑使用性能监控工具分析瓶颈 