# SpotLight - 混合驱动Android虚拟机自动化操作平台

## 项目概述

SpotLight 是一个基于云服务器的混合驱动Android虚拟机自动化操作平台，专门用于操作微信小程序和WebView应用。通过支持多种WebDriver实现（Selenium、Appium），实现云端脚本服务与Android虚拟机应用的协同工作，为用户提供智能化的应用操作服务。

## 系统架构

### 整体架构图
```
用户指令 → Android虚拟机APP → 云服务器Script服务 → 混合WebDriver → 微信小程序/WebView
```

### 核心组件

#### 1. 云服务器 (Cloud Server)
- **操作系统**: Linux
- **部署环境**: Python 3.8+
- **服务框架**: FastAPI + Uvicorn
- **主要功能**: 运行混合驱动服务，管理多个Android虚拟机连接

#### 2. Android虚拟机 (Android Emulator)
- **模拟器**: Google Android Emulator
- **系统版本**: Android 8.0+
- **网络配置**: 与云服务器通过HTTP API通信
- **主要功能**: 运行目标应用（微信、小程序等）

#### 3. Android APP (aidaemon)
- **运行环境**: Android虚拟机
- **通信协议**: HTTP RESTful API
- **主要功能**: 
  - 接收用户指令
  - 与云服务器混合驱动服务通信
  - 管理本地应用状态
  - 提供操作反馈

#### 4. 混合驱动服务 (hybrid_driver/)
- **运行环境**: 云服务器
- **技术栈**: Python + FastAPI + 混合WebDriver
- **主要功能**:
  - 管理Android设备连接池
  - 支持多种WebDriver实现（Selenium、Appium）
  - 执行WebDriver自动化操作
  - 处理微信小程序和WebView操作
  - 提供RESTful API接口

## 技术架构详解

### 1. 设备管理层 (Device Management)

#### DevicePool (设备池)
```python
# 单例模式，管理多个Android设备连接
class DevicePool:
    - 设备连接管理
    - 连接状态监控
    - 自动清理机制
    - 线程安全操作
```

#### AndroidDevice (设备抽象)
```python
# 封装单个Android设备的操作接口
class AndroidDevice:
    - ADB设备连接
    - 混合WebDriver管理
    - 元素查找和操作
    - 页面状态管理
```

### 2. 混合WebDriver执行层 (Hybrid WebDriver Execution)

#### WebExecutor接口 (抽象基类)
```python
# 定义所有WebDriver实现必须遵循的接口
class WebExecutor(ABC):
    - connect(device_id: str) -> bool
    - find_element(by: str, value: str) -> Optional[WebElement]
    - wait_for_element(by: str, value: str, timeout: int) -> Optional[WebElement]
    - execute_script(script: str, *args) -> Any
```

#### SeleniumWebExecutor (Selenium实现)
```python
# 基于Selenium的WebDriver实现
class SeleniumWebExecutor(WebExecutor):
    - Chrome WebDriver连接管理
    - 微信小程序WebView操作
    - 元素定位和交互
    - 页面导航和状态管理
```

#### AppiumExecutor (Appium实现)
```python
# 基于Appium的WebDriver实现
class AppiumExecutor:
    - Appium Server连接管理
    - 原生Android应用操作
    - 混合应用支持
    - 上下文切换管理
```

#### 操作指令系统 (Operation System)
```python
# 支持多种操作类型的指令系统
- ACTION_CLICK: 点击操作
- ACTION_SET_TEXT: 文本输入
- ACTION_COLLECT_ITEM_INFO: 数据收集
- ACTION_TEST: 验证测试
- ACTION_OPEN_HOME: 打开首页
```

### 3. API服务层 (API Service)

#### FastAPI服务
```python
# RESTful API接口
- POST /connect: 连接设备
- POST /disconnect: 断开设备
- POST /action: 执行操作
- POST /find_element: 查找元素
- POST /run_operations: 执行操作序列
```

## 项目结构

```
spot_light/
├── hybrid_driver/                    # 混合驱动服务核心
│   ├── main.py                       # 服务入口
│   ├── server.py                     # FastAPI服务器
│   ├── device_pool.py                # 设备池管理
│   ├── device/                       # 设备抽象层
│   │   ├── __init__.py
│   │   └── android_device.py         # Android设备封装
│   ├── webdriver/                    # 混合WebDriver实现
│   │   ├── __init__.py
│   │   ├── base.py                   # WebDriver基类
│   │   ├── web_executor.py           # Web执行器接口
│   │   ├── selenium_executor.py      # Selenium执行器
│   │   ├── appium_executor.py        # Appium执行器
│   │   ├── webdriver_utils.py        # WebDriver工具
│   │   ├── wait_utils.py             # 等待工具
│   │   ├── popup_handler.py          # 弹窗处理器
│   │   └── pool.py                   # WebDriver连接池
│   ├── operation.py                  # 操作指令系统
│   ├── utils/                        # 工具模块
│   │   └── logger.py                 # 日志工具
│   ├── tests/                        # 测试用例
│   ├── logs/                         # 日志文件
│   ├── demo/                         # 演示代码
│   ├── requirements.txt              # Python依赖
│   └── setup.py                      # 安装配置
├── aidaemon/                         # Android虚拟机APP (不修改)
├── uploads/                          # 上传文件目录
├── docs/                             # 项目文档
├── docker/                           # Docker配置
├── requirements.txt                  # 项目依赖
├── README.md                         # 项目说明
├── ARCHITECTURE.md                   # 架构文档
├── DEPLOYMENT.md                     # 部署指南
├── API.md                           # API文档
├── Instruction.MD                    # 操作指令说明
└── DEV_TOOLS_RECOMMEND.md           # 开发工具推荐
```

## 核心功能特性

### 1. 混合驱动支持
- 支持Selenium WebDriver（WebView操作）
- 支持Appium WebDriver（原生应用操作）
- 可扩展的WebDriver接口设计
- 自动选择合适的驱动实现

### 2. 多设备并发管理
- 支持同时连接多个Android虚拟机
- 设备池自动管理和资源回收
- 连接状态监控和故障恢复
- 线程安全的设备管理

### 3. 智能操作指令
- 支持复杂的操作序列
- 参数化操作和数据驱动
- 条件判断和异常处理
- 操作结果验证和反馈

### 4. 微信小程序支持
- 原生微信小程序WebView操作
- 小程序页面路由管理
- 弹窗自动处理
- 数据采集和验证

### 5. 高可用性设计
- 线程安全的设备管理
- 自动重连和故障恢复
- 详细的日志记录和监控
- 优雅的资源清理

## 快速开始

### ⚠️ LiveEdit 兼容性说明

在使用 WebCommand 功能时，如果遇到以下错误：

```
K: LiveEdit: Could not instantiate superclass
java.lang.reflect.InvocationTargetException
Caused by: java.lang.IllegalArgumentException: Unhandled superclass: kotlin/coroutines/jvm/internal/ContinuationImpl
```

**解决方案**：
1. 在 Android Studio 中禁用 LiveEdit 功能
2. 使用传统构建方式（Run 而不是 Apply Changes）
3. 详细说明请参考：[LiveEdit 兼容性文档](aidaemon/execution/src/main/java/ai/guangfan/execution/command/LIVEEDIT_COMPATIBILITY.md)

### 环境准备

#### 系统要求
```bash
# 操作系统
- Ubuntu 20.04 LTS / CentOS 8+
- Python 3.8+
- Chrome/Chromium浏览器
- ADB工具
- Appium Server (可选)

# 网络要求
- 与Android虚拟机网络连通
- HTTP API端口开放
```

#### 安装依赖
```bash
# 克隆项目
git clone <repository_url>
cd spot_light

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt
cd hybrid_driver
pip install -r requirements.txt
```

### 2. 配置服务

```bash
# 创建配置文件
cat > .env << EOF
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
CHROME_VERSION=134.0.6998.136
ANDROID_PACKAGE=com.tencent.mm
APPIUM_SERVER_URL=http://localhost:4723
EOF

# 创建必要目录
mkdir -p logs uploads
```

### 3. 启动服务

```bash
# 开发模式
cd hybrid_driver
python main.py

# 生产模式
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 测试连接

```bash
# 测试健康检查
curl http://localhost:8000/health

# 测试设备连接
curl -X POST http://localhost:8000/connect \
  -H "Content-Type: application/json" \
  -d '{"serial_id": "test_device"}'
```

## API接口文档

### 设备管理接口

#### 连接设备
```http
POST /connect
Content-Type: application/json

{
  "serial_id": "device_serial_id"
}
```

#### 断开设备
```http
POST /disconnect
Content-Type: application/json

{
  "serial_id": "device_serial_id"
}
```

### 操作执行接口

#### 执行单个操作
```http
POST /action
Content-Type: application/json

{
  "serial_id": "device_serial_id",
  "type": "click",
  "params": {
    "selector": "#button"
  }
}
```

#### 执行操作序列
```http
POST /run_operations
Content-Type: application/json

{
  "serial_id": "device_serial_id",
  "operations": [
    {
      "type": "click",
      "method": "css selector",
      "selector": "#button",
      "timeout": 10
    }
  ]
}
```

## 测试指南

### 1. 单元测试
```bash
# 运行所有测试
cd hybrid_driver
PYTHONPATH=. pytest tests/

# 运行指定测试
PYTHONPATH=. pytest tests/test_web_driver.py

# 显示详细日志
PYTHONPATH=. pytest tests/ -s --log-cli-level=INFO
```

### 2. 集成测试
```bash
# 启动测试服务
cd hybrid_driver
python main.py

# 测试设备连接
curl -X POST http://localhost:8000/connect \
  -H "Content-Type: application/json" \
  -d '{"serial_id": "test_device"}'
```

## 监控和日志

### 1. 日志配置
- 日志级别: INFO/DEBUG/ERROR
- 日志格式: 时间戳 + 级别 + 模块 + 消息
- 日志轮转: 按大小和时间自动轮转

### 2. 监控指标
- 设备连接状态
- 操作执行成功率
- 响应时间统计
- 错误率监控

### 3. 健康检查
```http
GET /health
```

## 故障排除

### 1. 常见问题

#### 设备连接失败
- 检查ADB连接状态
- 验证设备序列号
- 确认网络连通性

#### WebDriver初始化失败
- 检查Chrome/Chromium安装
- 验证ChromeDriver版本
- 确认端口占用情况
- 检查Appium Server状态（如果使用Appium）

#### 操作执行超时
- 检查网络延迟
- 验证元素定位器
- 确认页面加载状态

### 2. 调试技巧
- 启用DEBUG日志级别
- 使用浏览器开发者工具
- 检查ADB日志输出
- 查看Appium日志（如果使用Appium）

## 开发指南

### 1. 添加新的WebDriver实现
```python
from hybrid_driver.webdriver.web_executor import WebExecutor

class CustomWebExecutor(WebExecutor):
    def connect(self, device_id: str, **kwargs) -> bool:
        # 实现连接逻辑
        pass
    
    def find_element(self, by: str, value: str) -> Optional[WebElement]:
        # 实现元素查找逻辑
        pass
```

### 2. 添加新的操作类型
```python
from hybrid_driver.operation import OperationRegistry

@OperationRegistry.register("custom_action")
class CustomAction(Operation):
    def __init__(self, **kwargs):
        # 初始化参数
        
    def execute(self, device, context=None):
        # 实现操作逻辑
        pass
```

### 3. 添加新的API接口
```python
@app.post("/custom_endpoint")
def custom_endpoint(req: CustomRequest):
    # 实现接口逻辑
    pass
```

## 性能优化

### 1. 连接池优化
- 实现连接复用
- 添加连接超时机制
- 优化资源清理策略

### 2. 操作优化
- 批量操作支持
- 异步操作处理
- 缓存机制优化

### 3. 内存管理
- 及时释放WebDriver资源
- 优化大对象生命周期
- 监控内存使用情况

## 安全考虑

### 1. 网络安全
- 使用HTTPS协议
- 实现身份认证
- 添加请求限流

### 2. 数据安全
- 敏感信息加密
- 日志脱敏处理
- 访问权限控制

## 版本历史

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础设备管理功能
- Selenium WebDriver支持
- RESTful API接口

### v1.1.0 (2024-02-01)
- 添加Appium WebDriver支持
- 混合驱动架构设计
- 优化设备池管理
- 增强错误处理

### v2.0.0 (2024-03-01)
- 重构为混合驱动架构
- 支持多种WebDriver实现
- 改进项目结构
- 增强可扩展性

## 相关文档

- **[架构文档](ARCHITECTURE.md)** - 详细的系统架构设计说明
- **[部署指南](DEPLOYMENT.md)** - 完整的部署和运维指南
- **[API文档](API.md)** - 完整的API接口文档和示例
- **[操作指令说明](Instruction.MD)** - 操作指令系统的详细说明
- **[开发工具推荐](DEV_TOOLS_RECOMMEND.md)** - 推荐的开发工具和环境配置

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request

## 许可证

MIT License

## 联系方式

- 项目维护者: [维护者信息]
- 邮箱: [联系邮箱]
- 项目地址: [项目URL]

---

**注意**: 本项目仅用于学习和研究目的，请遵守相关法律法规和平台使用条款。
