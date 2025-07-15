# 自定义 Selenium Chrome 镜像使用指南

## 概述

这个自定义镜像基于 `selenium/standalone-chrome:4.34.0-20250707`，在容器启动时会执行自定义的 shell 脚本，并支持外部传入参数。

## 文件结构

```
mini/docker/
├── Dockerfile.custom-selenium-chrome    # 自定义镜像 Dockerfile
├── docker-compose.custom-selenium.yml   # Docker Compose 配置
├── scripts/
│   └── custom_startup.sh               # 自定义启动脚本
└── README.custom-selenium.md           # 本说明文档
```

## 特性

- ✅ 继承自 `selenium/standalone-chrome:4.34.0-20250707`
- ✅ 容器启动时立即执行自定义脚本
- ✅ 支持外部传入参数
- ✅ 脚本从工程中复制到镜像
- ✅ 无需持久化和挂载（可选）
- ✅ 完整的日志记录
- ✅ 健康检查支持

## 快速开始

### 1. 构建镜像

```bash
cd mini/docker
docker compose -f docker-compose.custom-selenium.yml build
```

### 2. 启动服务

```bash
# 启动生产模式实例
docker compose -f docker-compose.custom-selenium.yml up -d custom-selenium-chrome

# 启动调试模式实例
docker compose -f docker-compose.custom-selenium.yml up -d custom-selenium-chrome-debug
```

### 3. 查看日志

```bash
# 查看生产模式日志
docker compose -f docker-compose.custom-selenium.yml logs -f custom-selenium-chrome

# 查看调试模式日志
docker compose -f docker-compose.custom-selenium.yml logs -f custom-selenium-chrome-debug
```

### 4. 停止服务

```bash
docker compose -f docker-compose.custom-selenium.yml down
```

## 自定义脚本参数

自定义启动脚本支持以下参数：

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--mode` | 运行模式 | 默认模式 | `--mode production` |
| `--timeout` | 超时时间（秒） | 30 | `--timeout 60` |
| `--log-level` | 日志级别 | INFO | `--log-level DEBUG` |
| `--help` | 显示帮助信息 | - | `--help` |

### 运行模式说明

- **默认模式**: 使用标准配置
- **debug**: 启用详细日志和调试功能
- **production**: 优化性能设置
- **test**: 启用测试配置

## 使用示例

### 1. 基本使用

```bash
# 使用默认参数启动
docker run -d -p 4444:4444 custom-selenium-chrome

# 传递自定义参数
docker run -d -p 4444:4444 custom-selenium-chrome --mode production --timeout 60
```

### 2. 使用 Docker Compose

```yaml
version: '3.8'
services:
  my-selenium:
    build:
      context: .
      dockerfile: Dockerfile.custom-selenium-chrome
    ports:
      - "4444:4444"
    command: 
      - "--mode"
      - "production"
      - "--timeout"
      - "60"
```

### 3. 在您的项目中使用

如果您想在 SpotLight 项目中使用这个自定义镜像，可以修改现有的 docker-compose 配置：

```yaml
# 在 mini/docker-compose-production.yml 中添加
services:
  selenium-chrome:
    build:
      context: ./docker
      dockerfile: Dockerfile.custom-selenium-chrome
    # ... 其他配置
```

## 自定义脚本开发

### 1. 修改启动脚本

编辑 `mini/docker/scripts/custom_startup.sh` 文件，添加您的自定义逻辑：

```bash
#!/bin/bash
set -e

# 您的自定义逻辑
echo "执行自定义初始化..."

# 设置环境变量
export MY_CUSTOM_VAR="value"

# 执行其他操作
# ...

echo "自定义初始化完成"
```

### 2. 添加新的参数

在脚本中添加新的参数解析：

```bash
while [[ $# -gt 0 ]]; do
    case $1 in
        --my-param)
            MY_PARAM="$2"
            shift 2
            ;;
        # ... 其他参数
    esac
done
```

### 3. 重新构建镜像

修改脚本后需要重新构建镜像：

```bash
docker compose -f docker-compose.custom-selenium.yml build --no-cache
```

## 环境变量

### Selenium 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SE_NODE_MAX_SESSIONS` | 最大会话数 | 4 |
| `SE_NODE_SESSION_TIMEOUT` | 会话超时时间 | 300 |
| `SE_CHROME_ARGS` | Chrome 启动参数 | - |

### 自定义环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `CUSTOM_MODE` | 运行模式 | - |
| `CUSTOM_TIMEOUT` | 超时时间 | 30 |
| `CUSTOM_LOG_LEVEL` | 日志级别 | INFO |

## 故障排除

### 1. 脚本执行失败

检查脚本权限和语法：

```bash
# 检查脚本权限
ls -la mini/docker/scripts/custom_startup.sh

# 检查脚本语法
bash -n mini/docker/scripts/custom_startup.sh
```

### 2. 参数传递问题

确保参数格式正确：

```bash
# 正确的参数格式
docker run custom-selenium-chrome --mode production --timeout 60

# 错误的参数格式
docker run custom-selenium-chrome --mode=production --timeout=60
```

### 3. 日志查看

```bash
# 查看容器日志
docker logs custom-selenium-chrome

# 查看启动脚本日志
docker exec custom-selenium-chrome cat /opt/scripts/logs/startup.log
```

## 性能优化

### 1. 内存配置

```yaml
services:
  custom-selenium-chrome:
    shm_size: 2gb  # 增加共享内存
    mem_limit: 4g   # 限制内存使用
```

### 2. 并发配置

```yaml
services:
  custom-selenium-chrome:
    environment:
      - SE_NODE_MAX_SESSIONS=8  # 增加并发会话数
```

## 安全考虑

1. **用户权限**: 容器以非 root 用户运行
2. **网络安全**: 只暴露必要的端口
3. **资源限制**: 设置内存和 CPU 限制
4. **日志安全**: 避免在日志中记录敏感信息

## 集成到 SpotLight 项目

要将此自定义镜像集成到您的 SpotLight 项目中：

1. 将文件复制到项目目录
2. 修改现有的 docker-compose 配置
3. 更新启动脚本以使用新的镜像
4. 测试集成是否正常工作

## 支持

如有问题，请查看：
- 容器日志: `docker logs <container_name>`
- 启动脚本日志: `/opt/scripts/logs/startup.log`
- 项目文档: `mini/README.md` 