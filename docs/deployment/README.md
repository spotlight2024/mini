# SpotLight 部署文档索引

## 📚 部署指南

### 🚀 快速开始
- **[快速启动指南](../quick-start.md)** - 最简洁的部署步骤，适合有经验的开发者
- **[完整部署指南](../deployment-guide.md)** - 详细的部署说明，包含故障排除和优化建议

### 🛠️ 部署工具
- **[统一启动脚本](../../scripts/spotlight.sh)** - 本地部署的标准化启动脚本
- **[部署状态检查](../../scripts/check-deployment.sh)** - 验证部署状态的诊断工具
- **[Docker配置文件](../../docker-compose.api.yml)** - API服务的Docker Compose配置
- **[Docker镜像构建](../../Dockerfile.spotlight)** - API服务的Docker镜像定义

## 🏗️ 部署架构

### 本地部署架构
```
┌─────────────────────────────────────────────────────────┐
│                   本地部署架构                          │
├─────────────────────────────────────────────────────────┤
│  📱 用户终端                                           │
│  ├── 浏览器访问: http://127.0.0.1:10001/docs          │
│  └── API调用: http://127.0.0.1:10001/api/*            │
├─────────────────────────────────────────────────────────┤
│  🐍 Python环境                                         │
│  ├── 虚拟环境: venv/                                   │
│  ├── 依赖管理: pyproject.toml / poetry.lock            │
│  └── 启动方式: scripts/spotlight.sh                    │
├─────────────────────────────────────────────────────────┤
│  🔧 核心服务                                           │
│  ├── FastAPI应用: hybrid_driver.server_optimized:app   │
│  ├── 端口监听: 10001 (可配置)                          │
│  └── 进程管理: uvicorn                                 │
└─────────────────────────────────────────────────────────┘
```

### Docker部署架构
```
┌─────────────────────────────────────────────────────────┐
│                   Docker部署架构                        │
├─────────────────────────────────────────────────────────┤
│  📱 用户终端                                           │
│  ├── 浏览器访问: http://127.0.0.1:10001/docs          │
│  └── API调用: http://127.0.0.1:10001/api/*            │
├─────────────────────────────────────────────────────────┤
│  🐳 Docker环境                                         │
│  ├── 镜像构建: Dockerfile.spotlight                    │
│  ├── 服务编排: docker-compose.api.yml                  │
│  └── 容器管理: docker compose                          │
├─────────────────────────────────────────────────────────┤
│  🔧 容器化服务                                         │
│  ├── 基础镜像: python:3.12-slim                        │
│  ├── 系统依赖: build-essential, android-tools-adb      │
│  ├── Python依赖: pyproject.toml / poetry.lock         │
│  ├── 应用代码: hybrid_driver/                          │
│  ├── 端口暴露: 10001                                   │
│  └── 健康检查: /health 端点                            │
└─────────────────────────────────────────────────────────┘
```

## 🔧 配置说明

### 环境变量配置
| 变量名      | 默认值    | 说明         | 本地部署 | Docker部署 |
| ----------- | --------- | ------------ | -------- | ---------- |
| `API_HOST`  | `0.0.0.0` | 服务监听地址 | ✅        | ✅          |
| `API_PORT`  | `10001`   | 服务监听端口 | ✅        | ✅          |
| `LOG_LEVEL` | `info`    | 日志级别     | ✅        | ✅          |

### 端口配置
- **默认端口**: 10001
- **端口范围**: 1024-65535 (建议使用1024以上)
- **配置方式**: 环境变量或启动参数
- **端口冲突**: 自动检测并提供解决方案

## 📋 部署检查清单

### 本地部署检查
- [ ] Python 3.12+ 已安装
- [ ] 虚拟环境已创建并激活
- [ ] 依赖包已安装完成
- [ ] 启动脚本有执行权限
- [ ] 端口10001未被占用
- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] API文档可访问

### Docker部署检查
- [ ] Docker服务正在运行
- [ ] Docker Compose已安装
- [ ] 镜像构建成功
- [ ] 容器启动成功
- [ ] 端口映射正确
- [ ] 健康检查通过
- [ ] 日志输出正常
- [ ] 资源使用合理

## 🚨 故障排除

### 常见问题速查
| 问题         | 症状                                  | 解决方案                                                   | 文档位置                                            |
| ------------ | ------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------- |
| 端口被占用   | `Address already in use`              | 使用`lsof -ti:10001 \| xargs kill -9`                      | [故障排除](../deployment-guide.md#故障排除)         |
| 权限不足     | `Permission denied`                   | 执行`chmod +x scripts/spotlight.sh`                        | [故障排除](../deployment-guide.md#故障排除)         |
| 依赖缺失     | `ModuleNotFoundError`                 | 重新安装依赖`poetry install --sync` | [环境准备](../deployment-guide.md#1-环境准备)       |
| Docker未启动 | `Cannot connect to the Docker daemon` | 启动Docker Desktop或Docker服务                             | [Docker环境准备](../deployment-guide.md#1-环境准备) |
| 构建失败     | `netifaces build failed`              | 确保Dockerfile包含`build-essential`                        | [Docker构建](../deployment-guide.md#2-构建镜像)     |

### 诊断工具
```bash
# 部署状态检查
./scripts/check-deployment.sh

# 仅检查本地部署
./scripts/check-deployment.sh --local

# 仅检查Docker部署
./scripts/check-deployment.sh --docker

# 检查特定端口
./scripts/check-deployment.sh --port 8080
```

## 📖 相关文档

### 核心架构
- [系统架构设计](../architecture/ARCHITECTURE.md)
- [三层架构整合](../architecture/THREE_LAYER_ARCHITECTURE.md)
- [API接口文档](../api/API.md)

### 开发指南
- [开发环境配置](../guides/DEV_TOOLS_RECOMMEND.md)
- [操作指令系统](../guides/Instruction.MD)
- [服务管理指南](../guides/SERVICE_MANAGEMENT.md)

### 容器化
- [自定义Selenium镜像](../../docker/README.custom-selenium.md)
- [ADB集成说明](../../docker/README.adb-integration.md)
- [集群部署方案](../../docker/README.adb-proxy.md)

## 🤝 技术支持

如果在部署过程中遇到问题：

1. **查看日志**: 检查`logs/`目录下的日志文件
2. **运行诊断**: 使用`./scripts/check-deployment.sh`进行状态检查
3. **查阅文档**: 参考本文档和相关技术文档
4. **搜索问题**: 在GitHub Issues中搜索相似问题
5. **提交反馈**: 创建新的Issue描述问题

---

**最后更新**: 2024年12月
**文档版本**: 1.0.0
