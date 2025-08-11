# SpotLight 部署指南

**注意**: 本文档基于SpotLight项目的最新版本编写，包含完整的服务启动方式和管理功能。

## 📋 目录

- [1. 环境准备](#1-环境准备)
- [2. 统一启动脚本](#2-统一启动脚本)
- [3. 本地部署](#3-本地部署)
- [4. Docker部署](#4-docker部署)
- [5. 本地服务管理](#5-本地服务管理)
- [6. 开发工作流](#6-开发工作流)
- [7. 故障排除](#7-故障排除)

## 1. 环境准备

### 1.1 系统要求
- **操作系统**: Linux, macOS, Windows
- **Python**: 3.8+ (推荐3.9+)
- **Docker**: 20.10+ (可选，用于容器化部署)
- **Docker Compose**: V2 (两个单词，不带连字符)
- **内存**: 最少2GB，推荐4GB+
- **磁盘**: 最少1GB可用空间

### 1.2 依赖安装
```bash
# 克隆项目
git clone <repository-url>
cd mini

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 1.3 环境检查
```bash
# 检查Python环境
python3 --version
pip --version

# 检查Docker环境（可选）
docker --version
docker compose version

# 检查脚本权限
chmod +x scripts/spotlight.sh
```

## 2. 统一启动脚本

### 2.1 脚本概览
SpotLight使用统一的启动脚本 `scripts/spotlight.sh` 来管理所有服务操作：

```bash
# 基本用法
./scripts/spotlight.sh [命令] [选项]

# 查看帮助
./scripts/spotlight.sh help
```

### 2.2 可用命令

#### 🚀 服务启动命令
- `dev` - 本地开发模式（热重载，后台运行）
- `serve` - 本地生产模式（多进程）
- `docker-dev` - Docker开发模式（代码挂载，热重载）
- `docker` - Docker生产模式（代码打包）

#### 🔧 本地服务管理命令
- `stop` - 停止本地服务
- `restart` - 重启本地服务
- `status-local` - 查看本地服务状态

#### 🔧 生产环境管理命令
- `build` - 构建生产镜像
- `deploy` - 部署到生产环境
- `update` - 更新代码并部署
- `status` - 查看部署状态
- `logs` - 查看服务日志
- `cleanup` - 清理Docker资源

## 3. 本地部署

### 3.1 开发模式启动
```bash
# 基本启动（后台运行）
./scripts/spotlight.sh dev

# 自定义端口和主机
./scripts/spotlight.sh dev --port 10002 --host 0.0.0.0

# 使用环境变量
export PORT=10002
export HOST=0.0.0.0
./scripts/spotlight.sh dev
```

**特点**：
- ✅ 支持热重载（代码修改自动重启）
- ✅ 后台运行（不占用终端）
- ✅ 自动日志记录到 `uvicorn.log`
- ✅ 进程ID跟踪和管理
- ✅ 外网可访问（默认绑定到0.0.0.0）

### 3.2 生产模式启动
```bash
# 基本启动
./scripts/spotlight.sh serve

# 自定义配置
./scripts/spotlight.sh serve --port 10001 --workers 4 --log-level info

# 使用环境变量
export API_PORT=10001
export API_HOST=0.0.0.0
export LOG_LEVEL=info
./scripts/spotlight.sh serve
```

**特点**：
- ✅ 多进程支持（可配置worker数量）
- ✅ 生产级性能优化
- ✅ 后台运行
- ✅ 自动日志记录

### 3.3 启动后信息
启动成功后，脚本会显示：
```
✅ 服务已成功启动在后台
🌐 Service: http://0.0.0.0:10001
📚 API Docs: http://0.0.0.0:10001/docs
💚 Health: http://0.0.0.0:10001/health
📝 Logs: tail -f uvicorn.log
🛑 Stop: kill <PID>
```

## 4. Docker部署

### 4.1 开发环境（代码挂载）
```bash
# 启动开发容器
./scripts/spotlight.sh docker-dev

# 自定义端口
./scripts/spotlight.sh docker-dev --port 10002

# 使用环境变量
export API_PORT=10002
./scripts/spotlight.sh docker-dev
```

**特点**：
- ✅ 代码目录挂载到容器
- ✅ 支持代码修改后自动重载
- ✅ 无需重新构建镜像
- ✅ 适合本地开发和调试
- ✅ 环境隔离，依赖管理简单

### 4.2 生产环境
```bash
# 启动生产容器
./scripts/spotlight.sh docker

# 自定义端口
./scripts/spotlight.sh docker --port 10001

# 使用环境变量
export API_PORT=10001
export LOG_LEVEL=info
./scripts/spotlight.sh docker
```

**特点**：
- ✅ 代码打包到镜像中
- ✅ 性能更好，更稳定
- ✅ 适合生产环境部署
- ✅ 版本控制和回滚支持

### 4.3 Docker环境要求
```bash
# 检查Docker状态
docker info

# 检查Docker Compose
docker compose version

# 启动Docker服务（如果未运行）
sudo systemctl start docker  # Linux
# 或启动Docker Desktop (macOS/Windows)
```

## 5. 本地服务管理

### 5.1 查看服务状态
```bash
# 查看本地服务状态
./scripts/spotlight.sh status-local
```

**输出示例**：
```
[STATUS-LOCAL] 本地服务状态:
  ✅ 本地服务正在运行
  📊 进程ID: 171148
  🌐 监听地址: tcp 0 0 0.0.0.0:10001 0.0.0.0:* LISTEN 171148/python3
🌐 Service: http://localhost:10001
📚 API Docs: http://localhost:10001/docs
💚 Health: http://localhost:10001/health
📝 Logs: tail -f uvicorn.log
🛑 Stop: ./scripts/spotlight.sh stop
🔄 Restart: ./scripts/spotlight.sh restart
```

### 5.2 停止服务
```bash
# 停止本地服务
./scripts/spotlight.sh stop
```

**特点**：
- ✅ 优雅退出（先发送SIGTERM信号）
- ✅ 超时保护（10秒后强制终止）
- ✅ 进程状态验证
- ✅ 详细操作反馈

### 5.3 重启服务
```bash
# 重启本地服务
./scripts/spotlight.sh restart
```

**特点**：
- ✅ 自动停止现有服务
- ✅ 等待端口释放
- ✅ 重新启动服务
- ✅ 启动状态验证
- ✅ 配置继承（使用当前环境变量）

### 5.4 进程管理
```bash
# 查看运行中的uvicorn进程
ps aux | grep uvicorn

# 查看端口占用
netstat -tlnp | grep :10001

# 查看服务日志
tail -f uvicorn.log

# 手动停止进程（如果脚本无法停止）
kill -9 <PID>
```

## 6. 开发工作流

### 6.1 本地开发流程
```bash
# 1. 启动开发服务
./scripts/spotlight.sh dev

# 2. 修改代码（自动重载）

# 3. 测试API
curl http://localhost:10001/health
curl http://localhost:10001/docs

# 4. 查看日志
tail -f uvicorn.log

# 5. 停止服务
./scripts/spotlight.sh stop

# 6. 重启服务（如果需要）
./scripts/spotlight.sh restart
```

### 6.2 Docker开发流程
```bash
# 1. 启动Docker开发环境
./scripts/spotlight.sh docker-dev

# 2. 修改代码（自动重载）

# 3. 查看日志
docker compose -f docker-compose.dev.yml logs -f

# 4. 停止服务
docker compose -f docker-compose.dev.yml down

# 5. 重新启动
./scripts/spotlight.sh docker-dev
```

### 6.3 代码更新流程
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 更新依赖（如果有变化）
pip install -r requirements.txt

# 3. 重启服务
./scripts/spotlight.sh restart

# 4. 验证服务状态
./scripts/spotlight.sh status-local
curl http://localhost:10001/health
```

## 7. 故障排除

### 7.1 常见问题

| 问题 | 症状 | 解决方案 |
|------|------|----------|
| 端口被占用 | `Address already in use` | `./scripts/spotlight.sh stop` 或 `lsof -ti:10001 \| xargs kill -9` |
| 权限不足 | `Permission denied` | `chmod +x scripts/spotlight.sh` |
| 依赖缺失 | `ModuleNotFoundError` | `pip install -r requirements.txt` |
| 虚拟环境未激活 | `python3: command not found` | `source venv/bin/activate` |
| 服务无法外网访问 | 只能本地访问 | 检查host是否为0.0.0.0，检查防火墙设置 |
| 进程无法停止 | 脚本停止失败 | `ps aux \| grep uvicorn` 然后 `kill -9 <PID>` |

### 7.2 日志查看
```bash
# 本地服务日志
tail -f uvicorn.log

# Docker开发环境日志
docker compose -f docker-compose.dev.yml logs -f

# Docker生产环境日志
docker compose -f docker-compose.api.yml logs -f

# 实时查看日志
tail -f uvicorn.log | grep -E "(ERROR|WARNING|INFO)"
```

### 7.3 健康检查
```bash
# 检查服务状态
curl http://localhost:10001/health

# 检查API文档
curl http://localhost:10001/docs

# 检查端口监听
netstat -tlnp | grep :10001

# 检查进程状态
./scripts/spotlight.sh status-local
```

### 7.4 网络问题排查
```bash
# 检查本地访问
curl http://127.0.0.1:10001/health

# 检查外网访问
curl http://$(hostname -I | awk '{print $1}'):10001/health

# 检查防火墙状态
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS/RHEL

# 检查SELinux状态
sestatus
```

## 🔧 配置文件说明

### 环境变量
- `API_HOST` / `HOST`: 服务监听地址（默认：0.0.0.0）
- `API_PORT` / `PORT`: 服务监听端口（默认：10001）
- `LOG_LEVEL`: 日志级别（默认：info）
- `ENVIRONMENT`: 运行环境（development/production）

### 配置文件
- `requirements.txt`: Python依赖包列表
- `docker-compose.dev.yml`: Docker开发环境配置
- `docker-compose.api.yml`: Docker生产环境配置
- `hybrid_driver/config/settings.py`: 应用配置文件

### 日志文件
- `uvicorn.log`: 本地服务运行日志
- Docker日志通过 `docker compose logs` 查看

## 📚 相关文档

- [快速启动指南](quick-start.md)
- [项目架构](../architecture/README.md)
- [API文档](../README.md#api-模块化设计)
- [开发工具推荐](dev-tools-recommend.md)

## 🆘 获取帮助

### 脚本帮助
```bash
# 查看完整帮助
./scripts/spotlight.sh help

# 查看特定命令帮助
./scripts/spotlight.sh dev --help
```

### 联系支持
- 查看项目README获取更多信息
- 提交Issue到项目仓库
- 联系开发团队

---

**最后更新**: 2024年12月  
**文档版本**: 3.0.0  
**适用版本**: SpotLight v2.0+
