# SpotLight Hybrid Driver Docker 部署

轻量级 Docker 容器化部署方案，仅包含 API 服务，不包含 Selenium 相关组件。

## 目录结构

```
docker/
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # 生产环境配置
├── docker-compose.dev.yml  # 开发环境配置
├── env.example            # 环境变量示例
├── scripts/               # 管理脚本
│   ├── build.sh          # 构建镜像
│   ├── start.sh          # 启动服务
│   ├── stop.sh           # 停止服务
│   ├── status.sh         # 查看状态
│   └── dev.sh            # 启动开发环境
└── README.md             # 本文档
```

## 快速开始

### 1. 构建镜像

```bash
cd hybrid_driver/docker
./scripts/build.sh
```

### 2. 启动服务

```bash
# 生产环境
./scripts/start.sh

# 开发环境（支持热重载）
./scripts/dev.sh
```

### 3. 查看状态

```bash
./scripts/status.sh
```

### 4. 停止服务

```bash
./scripts/stop.sh
```

## 环境配置

### 复制环境变量文件

```bash
cp env.example .env
```

### 主要配置项

- `API_HOST`: API 服务主机地址（默认：0.0.0.0）
- `API_PORT`: API 服务端口（默认：10001）
- `LOG_LEVEL`: 日志级别（INFO/DEBUG）
- `WEBDRIVER_MODE`: WebDriver 模式（local/remote）

## 服务访问

启动成功后，可以通过以下地址访问：

- **API 文档**: http://localhost:10001/docs
- **健康检查**: http://localhost:10001/health
- **根路径**: http://localhost:10001/

## 开发环境特性

开发环境（`docker-compose.dev.yml`）提供以下特性：

- ✅ 代码热重载
- ✅ 源代码目录挂载
- ✅ 调试日志
- ✅ 快速重启

## 数据持久化

以下目录会被持久化存储：

- `./logs/` - 日志文件
- `./data/` - 数据文件
- `./cache/` - 缓存文件

## 常用命令

```bash
# 查看容器日志
docker compose logs -f

# 进入容器
docker compose exec spotlight-api bash

# 重启服务
docker compose restart

# 查看资源使用
docker stats
```

## 故障排除

### 1. 端口冲突

如果 10001 端口被占用，可以修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8080:10001"  # 将 8080 映射到容器内的 10001
```

### 2. 权限问题

确保脚本有执行权限：

```bash
chmod +x scripts/*.sh
```

### 3. 查看详细日志

```bash
docker compose logs --tail=100 -f
```

## 注意事项

1. 本方案为轻量级部署，不包含 Selenium Grid
2. 如需使用 WebDriver 功能，需要外部提供 Selenium 服务
3. 开发环境支持代码热重载，修改代码后会自动重启服务
4. 生产环境建议使用 `docker-compose.yml` 配置
