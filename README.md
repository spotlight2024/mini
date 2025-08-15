# SpotLight 混合驱动自动化平台

## 📋 项目概览

SpotLight 是一个面向 Android 虚拟机自动化的云端混合驱动平台，支持微信小程序/WebView/原生自动化，具备多设备并发、智能指令、弹窗处理、数据采集等能力。项目采用三层架构设计，将业务代码、容器化部署和 Selenium 修改有机整合，形成完整的自动化测试解决方案。

### 🏗️ 三大核心架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    SpotLight 平台架构                           │
├─────────────────────────────────────────────────────────────────┤
│  📱 业务代码层 (mini/)                                         │
│  ├── hybrid_driver/     # 核心服务实现                        │
│  ├── scripts/           # 管理脚本                            │
│  ├── tests/             # 测试用例                            │
│  └── docs/              # 详细文档                            │
├─────────────────────────────────────────────────────────────────┤
│  🐳 容器化架构层 (mini/docker/)                               │
│  ├── 自定义 Selenium 镜像                                      │
│  ├── ADB 集成功能                                           │
│  ├── 代理服务 (ADB Proxy)                                     │
│  └── 集群部署方案                                           │
├─────────────────────────────────────────────────────────────────┤
│  🔧 Selenium 修改层 (@/selenium/)                            │
│  ├── 协议扩展                                              │
│  ├── 参数增强                                              │
│  └── 功能定制                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境准备

```bash
# 1. 克隆项目
git clone <repository-url>
cd mini

# 2. 一键启动（推荐新手）
./scripts/spotlight.sh dev      # 本地开发模式，支持热重载

# 3. 验证启动
curl http://localhost:10001/health
```

### 🚀 一键启动

```bash
# 给脚本执行权限
chmod +x scripts/spotlight.sh

# 🖥️ 本地开发（推荐新手）
./scripts/spotlight.sh dev      # 开发模式，支持热重载

# 🐳 Docker开发（推荐团队）
./scripts/spotlight.sh docker-dev  # 代码挂载，支持热重载

# 🚀 生产部署
./scripts/spotlight.sh serve    # 本地生产模式
./scripts/spotlight.sh docker   # Docker生产模式

# 📖 查看帮助
./scripts/spotlight.sh --help
```

### ✅ 验证启动

```bash
# 健康检查
curl http://localhost:10001/health

# API文档
open http://localhost:10001/docs

# 部署状态检查
./scripts/check-deployment.sh
```

### 🔧 常用命令

| 命令                                | 说明                   | 适用场景     |
| ----------------------------------- | ---------------------- | ------------ |
| `./scripts/spotlight.sh dev`        | 本地开发（热重载）     | 个人开发调试 |
| `./scripts/spotlight.sh docker-dev` | Docker开发（代码挂载） | 团队协作开发 |
| `./scripts/spotlight.sh serve`      | 本地生产模式           | 本地测试部署 |
| `./scripts/spotlight.sh docker`     | Docker生产模式         | 生产环境部署 |

### 📚 快速参考

- **5分钟快速启动**: [快速启动指南](docs/quick-start.md)
- **完整部署流程**: [部署指南](docs/deployment-guide.md)
- **部署状态检查**: `./scripts/check-deployment.sh`
- **生产环境管理**: `./scripts/spotlight.sh --help`

---

## 📱 第一部分：业务代码层 (mini/)

### 核心服务架构

```
hybrid_driver/
├── server_optimized.py      # 🆕 优化后的FastAPI服务器（主入口）
├── server.py                # 兼容性保留（转发到server_optimized）
├── device_pool.py           # 设备池管理
├── operation.py             # 操作执行引擎
├── webdriver/               # WebDriver 实现
│   ├── selenium_executor.py    # Selenium 执行器
│   ├── appium_executor.py      # Appium 执行器
│   └── base.py                 # 基础接口
├── device/                  # 设备抽象
│   ├── android_device.py       # Android 设备实现
│   └── device.py               # 设备基类
├── api/                     # 🆕 模块化API（重构）
│   ├── routers/                 # 路由模块
│   │   ├── device.py            # 设备管理
│   │   ├── element.py           # 元素操作
│   │   ├── page.py              # 页面管理
│   │   ├── collect.py           # 数据收集
│   │   └── mock.py              # 模拟测试
│   ├── models.py                # 数据模型
│   └── utils.py                 # 工具函数
├── config/                  # 配置管理
│   └── settings.py              # 应用设置
├── utils/                    # 🆕 工具模块
├── collect/                  # 🆕 数据收集模块
├── native/                   # 🆕 原生脚本执行
└── load_test/                # 🆕 性能测试
```

### 🆕 最新架构改进

#### 1. 服务器优化
- **统一入口**: `server_optimized.py` 作为主服务器入口
- **兼容性保留**: `server.py` 保持向后兼容
- **模块化路由**: 按功能模块组织API路由
- **异步优化**: 完整的异步编程规范

#### 2. API模块化重构
```python
# 新的模块化API结构
from hybrid_driver.api.routers import device, element, page, collect, mock

# 设备管理
POST /device/connect      # 连接设备
POST /device/disconnect   # 断开设备
POST /device/action       # 执行设备操作

# 元素操作
POST /element/find        # 查找单个元素
POST /element/find_all    # 查找多个元素
POST /element/click       # 点击元素
POST /element/operations  # 执行操作序列

# 页面管理
POST /page/check          # 检查页面状态

# 数据收集
POST /collect/items       # 收集元素信息

# 模拟测试
POST /mock/click          # 模拟点击
```

#### 3. 混合驱动特性
- **🔀 双执行器支持**: 统一支持 Selenium 和 Appium
- **🏭 工厂模式**: 通过 `ExecutorFactory` 动态选择执行器
- **🛡️ 类型安全**: 统一的 `WebExecutor` 接口
- **🔄 向后兼容**: 保持现有 API 兼容性

### 使用示例

```python
# 使用 Selenium 执行器（默认）
device = AndroidDevice(serial_id, executor_type="selenium")

# 使用 Appium 执行器
device = AndroidDevice(serial_id, executor_type="appium", 
                      appium_server_url="http://localhost:4723")

# 连接设备
response = requests.post("http://localhost:10001/device/connect", json={
    "serial_id": "123.56.152.41:6529"
})

# 查找元素
response = requests.post("http://localhost:10001/element/find", json={
    "serial_id": "123.56.152.41:6529",
    "method": "css selector",
    "selector": ".my-class"
})
```

---

## 🐳 第二部分：容器化架构层 (mini/docker/)

### 容器化架构概览

```
mini/docker/
├── Dockerfile.spotlight              # 🆕 生产环境镜像
├── docker-compose.dev.yml            # 🆕 开发环境编排
├── docker-compose.api.yml            # 🆕 生产环境编排
├── Dockerfile.custom-selenium-chrome # 自定义 Selenium 镜像
├── docker-compose.custom-selenium.yml # 基础容器编排
├── docker-compose.custom-selenium-adb.yml # 带 ADB 的容器编排
├── docker-compose.adb-proxy.yml     # ADB 代理服务
├── scripts/
│   ├── custom_startup.sh            # 自定义启动脚本
│   ├── adb_init.sh                 # ADB 初始化脚本
│   └── proxy/                      # 代理服务
│       ├── adb_proxy.py            # ADB 代理实现
│       └── README.md               # 代理服务文档
└── build-adb-image.sh              # 镜像构建脚本
```

### 🆕 最新容器化特性

#### 1. 生产环境镜像
- **Dockerfile.spotlight**: 专门为生产环境优化的镜像
- **多阶段构建**: 优化镜像大小和安全性
- **健康检查**: 完整的容器健康监控
- **环境变量**: 灵活的配置管理

#### 2. 开发环境支持
```yaml
# docker-compose.dev.yml
services:
  spotlight-api-dev:
    build:
      context: .
      dockerfile: Dockerfile.spotlight
    volumes:
      # 代码挂载，支持热重载
      - ./hybrid_driver:/app/hybrid_driver
      - ./requirements:/app/requirements
    command: ["uvicorn", "hybrid_driver.server_optimized:app", "--reload"]
```

#### 3. 生产环境部署
```yaml
# docker-compose.api.yml
services:
  spotlight-api:
    build:
      context: .
      dockerfile: Dockerfile.spotlight
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
    restart: unless-stopped
```

### 🎯 核心功能特性

#### 1. 自定义 Selenium 镜像
- **基础镜像**: `selenium/standalone-chrome:4.34.0-20250707`
- **自定义脚本**: 容器启动时执行自定义 shell 脚本
- **参数支持**: 支持外部传入参数配置
- **健康检查**: 完整的容器健康监控

#### 2. ADB 集成功能
- **ADB 预装**: 镜像中预装 ADB 工具
- **自动初始化**: 容器启动时自动启动 ADB 服务器
- **设备连接**: 支持 USB 和网络设备连接
- **权限支持**: 支持 USB 设备访问（特权模式）

#### 3. ADB Proxy 代理服务
- **协议代理**: 监听本地端口，转发 ADB 请求
- **命令拦截**: 动态修改 ps 命令，实现进程过滤
- **多用户支持**: 支持多用户容器环境下的用户隔离
- **智能配置**: 支持动态 userId 传递和命令修改

### 🚀 快速部署

#### 1. 开发环境
```bash
cd mini
./scripts/spotlight.sh docker-dev
```

#### 2. 生产环境
```bash
cd mini
./scripts/spotlight.sh docker
```

#### 3. 自定义镜像
```bash
cd mini/docker
./build-adb-image.sh build
```

---

## 🔧 第三部分：Selenium 修改层 (@/selenium/)

### Selenium 项目结构

```
selenium/
├── py/                    # Python 绑定
├── java/                  # Java 绑定
├── javascript/            # JavaScript 绑定
├── dotnet/                # .NET 绑定
├── cpp/                   # C++ 绑定
├── rb/                    # Ruby 绑定
├── rust/                  # Rust 绑定
├── common/                # 通用组件
├── third_party/           # 第三方依赖
└── scripts/               # 构建脚本
```

### 🔄 协议扩展

#### 1. WebDriver 协议增强
- **自定义命令**: 扩展标准 WebDriver 协议
- **参数传递**: 支持额外的设备参数
- **状态管理**: 增强的设备状态管理
- **错误处理**: 改进的错误处理机制

#### 2. 设备参数扩展
```python
# 标准 capabilities
capabilities = {
    "platformName": "Android",
    "appium:automationName": "UiAutomator2",
    "appium:deviceName": "Pixel_5",
    "browserName": "chrome"
}

# 扩展 capabilities（SpotLight 特有）
capabilities.update({
    "se:userId": "u10_123",           # 用户隔离
    "se:devicePool": "pool1",         # 设备池
    "se:executorType": "selenium",     # 执行器类型
    "se:proxyEnabled": True,           # 代理启用
    "se:customParams": {               # 自定义参数
        "adbPort": 5037,
        "proxyPort": 5038
    }
})
```

---

## 🧪 测试和验证

### 测试结构
```
tests/
├── conftest.py            # 测试配置和共享夹具
├── unit/                  # 单元测试
├── integration/           # 集成测试
├── functional/            # 功能测试
└── fixtures/              # 测试数据和夹具
```

### 运行测试
```bash
# 运行所有测试
./start.sh test

# 运行特定测试
pytest tests/unit/           # 单元测试
pytest tests/integration/    # 集成测试
pytest tests/functional/     # 功能测试

# 运行压测
cd hybrid_driver/load_test
locust -f locustfile.py
```

### 容器测试
```bash
# 测试容器功能
cd mini/docker
./build-and-test.sh

# 测试 ADB 功能
./build-adb-image.sh test
```

---

## 🔄 异步接口规范

### FastAPI 路由规范
```python
@app.post("/api", response_model=APIResponse)
async def api_handler(req: RequestModel):
    # 纯异步 I/O
    await asyncio.sleep(1)
    
    # 阻塞操作必须用 run_sync 包裹
    result = await run_sync(blocking_func, req.param)
    
    return APIResponse(code=0, message="success", data=result)
```

### 线程池配置
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 设置全局线程池
executor = ThreadPoolExecutor(max_workers=20)
asyncio.get_event_loop().set_default_executor(executor)
```

---

## 📊 性能监控

### 压测指标
- **response_time**: 客户端观测到的总响应时间
- **process_time**: 服务端真实处理耗时
- **mock_delay**: 模拟的 sleep 时间
- **extra_delay**: 非业务延迟（网络、调度等）

### 监控命令
```bash
# 查看连接状态
netstat -an | grep 5037

# 查看容器资源
docker stats

# 查看代理日志
tail -f mini/docker/scripts/proxy/proxy.log
```

---

## 🔒 安全考虑

### 容器安全
- 临时文件权限控制
- 定期清理机制
- 内容验证

### 用户隔离
- userId 唯一性保证
- 会话隔离
- 资源清理

### 网络安全
- 端口访问控制
- 连接数限制
- 异常连接检测

---

## 🤝 贡献指南

### 代码规范
- 遵循 PEP 8 (Python)
- 添加适当的注释和文档
- 保持代码简洁可读

### 测试要求
- 新功能必须包含测试
- 保持测试覆盖率 > 80%
- 运行所有测试确保通过

### 提交规范
- 使用清晰的提交信息
- 包含相关的测试用例
- 更新相关文档

---

## 📞 联系方式

- **项目维护**: [维护者信息](docs/guides/contact.md)
- **问题反馈**: [GitHub Issues](https://github.com/your-repo/issues)
- **文档支持**: [详细文档](docs/README.md)
- **常见问题**: [FAQ](docs/guides/faq.md)

---

## 📝 更新日志

### v2.1.0 (2025-01-XX)
- ✅ **服务器优化**: 新增 `server_optimized.py` 作为主服务器入口
- ✅ **API模块化**: 重构API路由，按功能模块组织
- ✅ **容器化改进**: 新增生产环境镜像和开发环境支持
- ✅ **性能优化**: 优化异步处理和资源管理
- ✅ **测试完善**: 增强测试覆盖和性能测试

### v2.0.0 (2025-07-30)
- ✅ **三大架构整合**: 业务代码、容器化、Selenium 修改统一管理
- ✅ **ADB Proxy 服务**: 完整的用户隔离和命令修改功能
- ✅ **自定义 Selenium 镜像**: 支持 ADB 和自定义脚本
- ✅ **模块化 API 设计**: 清晰的 API 结构和路由组织
- ✅ **异步接口规范**: 完整的异步编程规范
- ✅ **容器化部署**: 完整的 Docker 部署方案

### v1.5.0 (2025-07-30)
- ✅ **执行器工厂模式**: 引入 `ExecutorFactory` 统一管理执行器
- ✅ **类型安全**: 统一 `WebExecutor` 接口，修复类型注解
- ✅ **API 模块化**: 将单文件服务器拆分为多个功能模块
- ✅ **向后兼容**: 保持现有 API 兼容性

---

## 📚 详细文档导航

### 📖 业务代码文档
- [📋 架构设计](docs/architecture/ARCHITECTURE.md) - 系统架构详解
- [🔌 API 文档](docs/api/API.md) - 完整API接口说明
- [📋 部署指南](docs/deployment-guide.md) - 完整部署和运维指南
- [🚀 快速启动](docs/quick-start.md) - 一键部署指南
- [🛠️ 开发工具](docs/guides/DEV_TOOLS_RECOMMEND.md) - 开发环境配置
- [📝 操作指令](docs/guides/Instruction.MD) - 操作指令系统说明
- [⚙️ 服务管理](docs/guides/SERVICE_MANAGEMENT.md) - 服务管理详细指南

### 🐳 容器化文档
- [🔧 自定义 Selenium](docker/README.custom-selenium.md) - 自定义镜像使用指南
- [📱 ADB 集成](docker/README.adb-integration.md) - ADB 功能集成说明
- [🔄 ADB Proxy](docker/scripts/proxy/README.md) - 代理服务详细文档
- [🏗️ 集群部署](docker/README.adb-proxy.md) - 集群部署方案

### 🔧 Selenium 修改文档
- [📋 贡献指南](selenium/CONTRIBUTING.md) - Selenium 贡献指南
- [🔧 构建说明](selenium/README.md) - Selenium 构建和部署
- [📚 API 文档](selenium/py/README.md) - Python 绑定文档

### 🏗️ 架构整合文档
- [📋 三大架构层整合](docs/architecture/THREE_LAYER_ARCHITECTURE.md) - 完整的三层架构整合说明

---

*最后更新时间: 2025-01-XX*

> 📖 **文档说明**: 所有详细文档已统一整理到对应目录，主 README 只保留项目概览和导航。如需查看详细内容，请访问对应的文档链接。
