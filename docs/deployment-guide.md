# SpotLight 部署指南

**注意**: 本文档基于SpotLight项目的最新版本编写，如有疑问请参考项目README或联系开发团队。

## 📋 目录

- [1. 环境准备](#1-环境准备)
- [2. 本地部署](#2-本地部署)
- [3. Docker部署](#3-docker部署)
- [4. 开发环境](#4-开发环境)
- [5. 生产环境代码更新](#5-生产环境代码更新)
- [6. 故障排除](#6-故障排除)

## 1. 环境准备

### 1.1 系统要求
- Python 3.8+
- Docker & Docker Compose (可选)
- Git

### 1.2 依赖安装
```bash
# 克隆项目
git clone <repository-url>
cd spot_light

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements/requirements.txt
```

## 2. 本地部署

### 2.1 快速启动
```bash
# 开发模式（支持热重载）
./scripts/spotlight.sh dev

# 生产模式
./scripts/spotlight.sh serve
```

### 2.2 自定义配置
```bash
# 指定端口和主机
./scripts/spotlight.sh dev --port 10002 --host 127.0.0.1

# 指定工作进程数和日志级别
./scripts/spotlight.sh serve --port 10001 --workers 4 --log-level debug
```

### 2.3 环境变量配置
```bash
# 设置环境变量
export API_PORT=10001
export API_HOST=0.0.0.0
export LOG_LEVEL=info

# 启动服务
./scripts/spotlight.sh serve
```

## 3. Docker部署

### 3.1 开发环境（代码挂载，支持热重载）
```bash
# 启动开发容器
./scripts/spotlight.sh docker-dev

# 自定义端口
./scripts/spotlight.sh docker-dev --port 10002
```

**特点**：
- 代码目录挂载到容器
- 支持代码修改后自动重载
- 无需重新构建镜像
- 适合本地开发和调试

### 3.2 生产环境
```bash
# 启动生产容器
./scripts/spotlight.sh docker

# 自定义端口
./scripts/spotlight.sh docker --port 10001
```

**特点**：
- 代码打包到镜像中
- 性能更好，更稳定
- 适合生产环境部署

### 3.3 环境变量配置
```bash
# 设置环境变量
export API_PORT=10001
export API_HOST=0.0.0.0
export LOG_LEVEL=info

# 启动Docker服务
./scripts/spotlight.sh docker
```

## 4. 开发环境

### 4.1 本地开发流程
```bash
# 1. 启动开发服务
./scripts/spotlight.sh dev

# 2. 修改代码（自动重载）

# 3. 测试API
curl http://localhost:10001/health

# 4. 停止服务
Ctrl+C
```

### 4.2 Docker开发流程
```bash
# 1. 启动Docker开发环境
./scripts/spotlight.sh docker-dev

# 2. 修改代码（自动重载）

# 3. 查看日志
docker compose -f docker-compose.dev.yml logs -f

# 4. 停止服务
docker compose -f docker-compose.dev.yml down
```

## 5. 生产环境代码更新

### 5.1 使用统一启动脚本（生产功能开发中）
```bash
# 构建并部署新版本（功能开发中）
./scripts/spotlight.sh update --tag v1.0.0

# 仅构建镜像（功能开发中）
./scripts/spotlight.sh build --tag v1.0.0

# 部署指定版本（功能开发中）
./scripts/spotlight.sh deploy --tag v1.0.0

# 查看部署状态
./scripts/spotlight.sh status

# 查看服务日志
./scripts/spotlight.sh logs [local|docker|docker-dev]
```

### 5.2 手动部署流程
```bash
# 1. 构建新镜像
docker build -t spotlight-api:v1.0.0 -f Dockerfile.spotlight .

# 2. 停止现有服务
docker compose -f docker-compose.api.yml down

# 3. 启动新服务
export API_PORT=10001
docker compose -f docker-compose.api.yml up -d

# 4. 验证部署
curl http://localhost:10001/health
```

### 5.3 版本管理
```bash
# 查看当前版本和状态
./scripts/spotlight.sh status

# 查看服务日志
./scripts/spotlight.sh logs docker

# 清理旧版本镜像
docker image prune -f
```

## 6. 故障排除

### 6.1 常见问题

| 问题         | 症状                                  | 解决方案                                                   |
| ------------ | ------------------------------------- | ---------------------------------------------------------- |
| 端口被占用   | `Address already in use`              | 使用`lsof -ti:10001 \| xargs kill -9`                      |
| 权限不足     | `Permission denied`                   | 执行`chmod +x scripts/spotlight.sh`                        |
| 依赖缺失     | `ModuleNotFoundError`                 | 重新安装依赖`pip install -r requirements/requirements.txt` |
| Docker未启动 | `Cannot connect to the Docker daemon` | 启动Docker Desktop或Docker服务                             |
| 构建失败     | `netifaces build failed`              | 确保Dockerfile包含`build-essential`                        |

### 6.2 日志查看
```bash
# 本地服务日志
# 直接在终端查看

# Docker开发环境日志
docker compose -f docker-compose.dev.yml logs -f

# Docker生产环境日志
docker compose -f docker-compose.api.yml logs -f

# 或使用部署脚本
./scripts/deploy.sh logs
```

### 6.3 健康检查
```bash
# 检查服务状态
curl http://localhost:10001/health

# 检查API文档
curl http://localhost:10001/docs

# 使用诊断脚本
./scripts/check-deployment.sh --local
./scripts/check-deployment.sh --docker
```

## 🔧 配置文件说明

### 环境变量
- `API_HOST`: 服务监听地址（默认：0.0.0.0）
- `API_PORT`: 服务监听端口（默认：10001）
- `LOG_LEVEL`: 日志级别（默认：info）
- `ENVIRONMENT`: 运行环境（development/production）

### Docker Compose文件
- `docker-compose.dev.yml`: 开发环境配置（代码挂载）
- `docker-compose.api.yml`: 生产环境配置（代码打包）

## 📚 相关文档

- [快速启动指南](quick-start.md)
- [API文档](../README.md#api-模块化设计)
- [项目架构](../architecture/README.md)

---

**最后更新**: 2024年12月
**文档版本**: 2.0.0
