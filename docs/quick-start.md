# SpotLight 快速启动指南

> 🚀 5分钟快速启动 SpotLight API 服务

## 📋 前置要求

- ✅ Python 3.8+
- ✅ Docker & Docker Compose (可选)
- ✅ Git

## 🚀 一键启动

### 方式一：本地启动（推荐新手）

```bash
# 1. 克隆项目
git clone <repository-url>
cd mini

# 2. 安装依赖
poetry install --with dev

# 3. 一键启动
chmod +x scripts/spotlight.sh
./scripts/spotlight.sh dev
```

### 方式二：Docker启动（推荐生产）

```bash
# 1. 克隆项目
git clone <repository-url>
cd mini

# 2. 一键启动
chmod +x scripts/spotlight.sh
./scripts/spotlight.sh docker
```

## ✅ 验证启动

```bash
# 健康检查
curl http://localhost:10001/health

# API文档
open http://localhost:10001/docs

# 服务状态
curl http://localhost:10001/
```

## 🔧 常用命令

### 开发环境
```bash
# 本地开发（热重载）
./scripts/spotlight.sh dev

# Docker开发（代码挂载，热重载）
./scripts/spotlight.sh docker-dev

# 自定义端口
./scripts/spotlight.sh dev --port 10002
./scripts/spotlight.sh docker-dev --port 10002
```

### 生产环境
```bash
# 本地生产
./scripts/spotlight.sh serve

# Docker生产
./scripts/spotlight.sh docker

# 自定义配置
./scripts/spotlight.sh serve --port 10001 --workers 4
./scripts/spotlight.sh docker --port 10001
```

### 环境变量配置
```bash
# 设置环境变量
export API_PORT=10001
export API_HOST=0.0.0.0
export LOG_LEVEL=info

# 启动服务
./scripts/spotlight.sh serve
```

## 🐳 Docker 开发工作流

### 快速调试
```bash
# 启动开发容器（代码挂载）
./scripts/spotlight.sh docker-dev

# 修改代码（自动重载）
# 无需重新构建镜像

# 查看日志
docker compose -f hybrid_driver/docker/docker-compose.dev.yml logs -f

# 停止服务
docker compose -f hybrid_driver/docker/docker-compose.dev.yml down
```

### 生产部署（功能开发中）
```bash
# 使用统一启动脚本
docker build -f hybrid_driver/docker/Dockerfile -t <registry>/spotlight-api:vX.Y.Z .
docker push <registry>/spotlight-api:vX.Y.Z

# 更新线上环境（Compose 为例）
docker compose -f hybrid_driver/docker/docker-compose.api.yml pull
docker compose -f hybrid_driver/docker/docker-compose.api.yml up -d

# 或 K8s
# kubectl set image deployment/spotlight-api spotlight-api=<registry>/spotlight-api:vX.Y.Z
# kubectl rollout status deployment/spotlight-api
```

## 🆘 快速故障排除

| 问题         | 快速解决                               |
| ------------ | -------------------------------------- |
| 端口被占用   | `lsof -ti:10001 \| xargs kill -9`      |
| 权限不足     | `chmod +x scripts/spotlight.sh`        |
| Docker未启动 | 启动 Docker Desktop                    |
| 构建失败     | 确保 Dockerfile 包含 `build-essential` |

## 📚 下一步

- 📖 [完整部署指南](deployment-guide.md)
- 🏗️ [项目架构](../architecture/README.md)
- 🔌 [API文档](../README.md#api-模块化设计)

---

**💡 提示**: 遇到问题？使用 `./scripts/check-deployment.sh` 进行诊断！
