# SpotLight 混合驱动服务架构文档

## 概述

本文档详细描述了SpotLight项目中混合驱动服务的内部架构设计，包括核心组件、数据流、接口设计和技术实现细节。

## 系统架构图

```
┌─────────────────┐    HTTP API    ┌─────────────────┐    WebDriver    ┌─────────────────┐
│   Android APP   │ ◄─────────────► │   混合驱动服务    │ ◄─────────────► │   混合WebDriver   │
│   (aidaemon)    │                 │  (hybrid_driver) │                 │  (Selenium/Appium)│
└─────────────────┘                 └─────────────────┘                 └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   微信小程序     │
                                    │   WebView       │
                                    └─────────────────┘
```

## 核心组件架构

### 1. 设备管理层 (Device Management Layer)

#### 1.1 DevicePool (设备池)
```python
class DevicePool:
    """
    单例模式的设备池管理器
    负责管理多个Android设备的连接和生命周期
    使用ExecutorFactory统一创建执行器
    """
    
    核心功能:
    - 设备连接管理 (connect/disconnect)
    - 连接状态监控 (is_connected)
    - 自动清理机制 (cleanup_task)
    - 线程安全操作 (threading.Lock)
    - 资源回收 (LRU策略)
    - 执行器工厂集成 (ExecutorFactory)
```

**设计特点:**
- 单例模式确保全局唯一性
- 线程安全的多设备并发管理
- 自动清理机制防止资源泄漏
- 支持设备连接状态监控
- 通过ExecutorFactory统一管理执行器创建

**设备创建流程:**
```python
# 使用ExecutorFactory创建设备，默认使用selenium执行器
device = AndroidDevice(serial_id, executor_type="selenium")
if device.connect(ip=ip, port=port):
    self.pool[serial_id] = device
```

#### 1.2 AndroidDevice (设备抽象)
```python
class AndroidDevice:
    """
    Android设备的抽象封装
    提供统一的设备操作接口
    支持多种执行器类型选择
    """
    
    核心功能:
    - ADB设备连接管理
    - 混合WebDriver实例管理（通过ExecutorFactory）
    - 元素查找和操作
    - 页面状态管理
    - 上下文管理器支持
    - 执行器类型选择（selenium/appium）
```

**设计特点:**
- 封装ADB和混合WebDriver的复杂性
- 提供统一的设备操作接口
- 支持连接状态检查
- 实现上下文管理器模式
- 通过工厂模式选择执行器类型
- 保持向后兼容性

**执行器选择机制:**
```python
# 使用工厂模式创建执行器
if self._web_execute_cls is not None:
    # 向后兼容：直接使用传入的类
    self._web_execute = self._web_execute_cls()
else:
    # 使用工厂模式
    self._web_execute = executor_factory.get_executor(
        self._executor_type,
        **self._executor_kwargs
    )
```

### 2. 混合WebDriver执行层 (Hybrid WebDriver Execution Layer)

#### 2.1 WebExecutor接口
```python
class WebExecutor(ABC):
    """
    WebDriver执行器的抽象接口
    定义所有WebDriver实现必须遵循的接口
    """
    
    核心方法:
    - connect(device_id: str) -> bool
    - quit() -> None
    - find_element(by: str, value: str) -> Optional[WebElement]
    - find_elements(by: str, value: str) -> Optional[List[WebElement]]
    - wait_for_element(by: str, value: str, timeout: int) -> Optional[WebElement]
    - execute_script(script: str, *args) -> Any
    - get_visible_pages(timeout: int) -> list
```

**设计特点:**
- 抽象基类定义统一接口
- 支持多种WebDriver实现
- 便于扩展和替换实现
- 类型安全的返回类型定义

#### 2.2 ExecutorFactory (执行器工厂)
```python
class ExecutorFactory:
    """
    执行器工厂类，统一管理不同类型的自动化执行器
    支持动态注册和获取执行器实例
    """
    
    核心功能:
    - 执行器注册 (register_executor)
    - 执行器获取 (get_executor)
    - 可用执行器查询 (get_available_executors)
    - 参数化执行器创建
```

**设计特点:**
- 工厂模式统一管理执行器
- 支持动态注册新的执行器类型
- 参数化创建，支持不同配置
- 类型安全的执行器选择

**使用示例:**
```python
# 获取 Selenium 执行器
selenium_executor = executor_factory.get_executor("selenium")

# 获取 Appium 执行器（带参数）
appium_executor = executor_factory.get_executor(
    "appium", 
    appium_server_url="http://localhost:4723",
    capabilities={"platformName": "Android"}
)

# 注册新的执行器类型
executor_factory.register_executor("custom", CustomExecutor)
```

#### 2.3 SeleniumWebExecutor (Selenium实现)
```python
class SeleniumWebExecutor(WebExecutor):
    """
    基于Selenium的WebDriver实现
    专门用于操作微信小程序WebView
    """
    
    核心功能:
    - Chrome WebDriver连接管理
    - 微信小程序WebView操作
    - 元素定位和交互
    - 页面导航和状态管理
    - 弹窗处理
```

**设计特点:**
- 基于Selenium WebDriver
- 支持微信小程序WebView
- 自动处理ChromeDriver管理
- 集成弹窗处理机制

#### 2.4 AppiumExecutor (Appium实现)
```python
class AppiumExecutor:
    """
    基于Appium的WebDriver实现
    支持原生Android应用和混合应用
    """
    
    核心功能:
    - Appium Server连接管理
    - 原生Android应用操作
    - 混合应用支持
    - 上下文切换管理
    - 元素定位和交互
```

**设计特点:**
- 基于Appium WebDriver
- 支持原生Android应用
- 支持混合应用（WebView + 原生）
- 上下文切换管理

### 3. 操作指令系统 (Operation System)

#### 3.1 Operation基类
```python
class Operation(ABC):
    """
    操作指令的抽象基类
    所有具体操作都继承自此类
    """
    
    @abstractmethod
    def execute(self, device, context=None):
        pass
```

#### 3.2 操作注册机制
```python
class OperationRegistry:
    """
    操作指令注册器
    支持动态注册和获取操作类型
    """
    
    核心功能:
    - 操作类型注册 (@register装饰器)
    - 操作类型获取 (get方法)
    - 所有操作类型查询 (all方法)
```

#### 3.3 核心操作类型

**基础操作:**
- `FindElement`: 元素查找
- `Click`: 点击操作
- `Input`: 文本输入
- `Wait`: 等待操作

**高级操作:**
- `WaitForNewWindow`: 等待新窗口
- `WaitForPageRender`: 等待页面渲染
- `HandlePopup`: 弹窗处理
- `JS`: JavaScript执行

**复合操作:**
- `Sequence`: 操作序列
- `If`: 条件操作
- `And/Or/Not`: 逻辑操作

### 4. API服务层 (API Service Layer)

#### 4.1 FastAPI服务
```python
app = FastAPI()
"""
基于FastAPI的RESTful API服务
提供设备管理和操作执行接口
"""
```

#### 4.2 核心API接口

**设备管理接口:**
- `POST /connect`: 连接设备
- `POST /disconnect`: 断开设备
- `GET /health`: 健康检查

**操作执行接口:**
- `POST /action`: 执行单个操作
- `POST /find_element`: 查找元素
- `POST /run_operations`: 执行操作序列

#### 4.3 请求/响应模型
```python
class APIResponse(BaseModel):
    """
    统一的API响应格式
    """
    code: int              # 响应码
    message: str           # 响应消息
    data: Optional[Any]    # 响应数据
    error: Optional[str]   # 错误信息
    trace_id: Optional[str] # 追踪ID
```

## 数据流设计

### 1. 设备连接流程
```
1. 客户端发送连接请求
   ↓
2. DevicePool接收请求
   ↓
3. 创建AndroidDevice实例
   ↓
4. 初始化混合WebDriver（Selenium或Appium）
   ↓
5. 连接WebDriver
   ↓
6. 返回连接结果
```

### 2. 操作执行流程
```
1. 客户端发送操作请求
   ↓
2. 解析操作指令
   ↓
3. 构建Operation实例
   ↓
4. 执行操作序列
   ↓
5. 返回执行结果
```

### 3. 资源管理流程
```
1. 定期清理任务启动
   ↓
2. 检查设备连接状态
   ↓
3. 清理无效连接
   ↓
4. 释放WebDriver资源
   ↓
5. 更新设备池状态
```

## 技术实现细节

### 1. 线程安全设计

#### 1.1 设备池线程安全
```python
class DevicePool:
    def __init__(self):
        self.lock = threading.Lock()  # 线程锁
    
    def connect(self, serial_id):
        with self.lock:  # 线程安全操作
            # 连接逻辑
            pass
```

#### 1.2 单例模式实现
```python
class DevicePool:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

### 2. 错误处理机制

#### 2.1 异常捕获和日志
```python
def execute(self, device, context=None):
    try:
        # 执行逻辑
        return result
    except Exception as e:
        logger.error(f"操作执行失败: {e}")
        return False
```

#### 2.2 连接重试机制
```python
def connect(self, serial_id, **kwargs) -> bool:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 连接逻辑
            return True
        except Exception as e:
            logger.warning(f"连接失败，重试 {attempt + 1}/{max_retries}: {e}")
            if attempt == max_retries - 1:
                raise
```

### 3. 资源管理

#### 3.1 自动清理机制
```python
def _start_cleanup_task(self, interval=600):
    """启动清理任务，定期清理空闲设备"""
    def task():
        while True:
            time.sleep(interval)
            try:
                with self.lock:
                    for serial_id in list(self.pool.keys()):
                        device = self.pool[serial_id]
                        if not device.is_connected():
                            self.disconnect(serial_id)
            except Exception as e:
                logger.error(f"清理任务异常: {e}")
    
    t = threading.Thread(target=task, daemon=True)
    t.start()
```

#### 3.2 上下文管理器
```python
class AndroidDevice:
    def __enter__(self):
        if not self.connect():
            raise RuntimeError(f"Failed to connect device: {self._serial_id}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
```

## 配置管理

### 1. 环境配置
```python
# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/spotlight.log")

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# WebDriver配置
CHROME_VERSION = os.getenv("CHROME_VERSION", "134.0.6998.136")
ANDROID_PACKAGE = os.getenv("ANDROID_PACKAGE", "com.tencent.mm")
APPIUM_SERVER_URL = os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")
```

### 2. 测试配置
```python
TEST_CONFIG = {
    "chrome_version": "134.0.6998.136",
    "ip": "172.16.1.125",
    "port": 6520,
    "device_serial": "test_serial",
    "android_process": "com.tencent.mm:appbrand0",
    "android_package": "com.tencent.mm",
    "appium_server_url": "http://localhost:4723"
}
```

## 性能优化

### 1. 连接池优化
- 实现连接复用机制
- 添加连接超时配置
- 优化资源清理策略

### 2. 操作优化
- 支持批量操作执行
- 实现异步操作处理
- 添加操作结果缓存

### 3. 内存管理
- 及时释放WebDriver资源
- 优化大对象生命周期
- 监控内存使用情况

## 安全考虑

### 1. 网络安全
- 使用HTTPS协议
- 实现身份认证机制
- 添加请求限流保护

### 2. 数据安全
- 敏感信息加密存储
- 日志脱敏处理
- 访问权限控制

### 3. 输入验证
- 严格的参数校验
- 防止注入攻击
- 安全的元素定位器

## 监控和日志

### 1. 日志系统
```python
# 结构化日志
logger.info(f"[{operation_name}] 操作执行", extra={
    "serial_id": serial_id,
    "operation": operation_type,
    "duration": duration
})
```

### 2. 监控指标
- 设备连接状态
- 操作执行成功率
- 响应时间统计
- 错误率监控

### 3. 健康检查
```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "device_count": len(device_pool.pool)
    }
```

## 扩展性设计

### 1. 插件化架构
- 操作类型可动态注册
- WebDriver实现可热插拔
- 支持自定义操作扩展

### 2. 配置化设计
- 环境配置外部化
- 支持多环境部署
- 动态配置更新

### 3. 模块化设计
- 清晰的模块边界
- 松耦合的组件设计
- 便于独立测试和维护

## 混合驱动特性

### 1. 多驱动支持
- **Selenium WebDriver**: 适用于WebView操作
- **Appium WebDriver**: 适用于原生应用和混合应用
- **可扩展接口**: 支持添加新的WebDriver实现

### 2. 驱动选择策略
```python
class DriverSelector:
    """
    根据应用类型和操作需求选择合适的WebDriver
    """
    
    def select_driver(self, app_type: str, operation_type: str):
        if app_type == "webview":
            return SeleniumWebExecutor()
        elif app_type == "native":
            return AppiumExecutor()
        elif app_type == "hybrid":
            # 根据具体操作选择
            if operation_type == "webview_operation":
                return SeleniumWebExecutor()
            else:
                return AppiumExecutor()
```

### 3. 上下文管理
```python
class ContextManager:
    """
    管理混合应用中的上下文切换
    """
    
    def switch_to_webview(self):
        # 切换到WebView上下文
        pass
    
    def switch_to_native(self):
        # 切换到原生上下文
        pass
```

## 项目架构文档

### 核心模块结构
```
spot_light/
├── hybrid_driver/                    # 混合驱动核心
│   ├── collect/                      # 数据采集模块
│   │   ├── __init__.py              # 采集模块入口
│   │   └── collect_items.py         # 元素信息采集实现
│   ├── operation.py                  # 操作指令系统
│   ├── server.py                     # HTTP服务接口
│   ├── device_pool.py               # 设备池管理
│   ├── webdriver/                    # WebDriver实现
│   │   ├── selenium_executor.py     # Selenium执行器
│   │   ├── appium_executor.py       # Appium执行器
│   │   └── webdriver_utils.py       # WebDriver工具
│   └── utils/                        # 工具模块
├── aidaemon/                         # Android虚拟机APP
└── docs/                             # 项目文档
```

### 数据采集模块 (collect/)
- **collect_items.py**: 实现ACTION_COLLECT_ITEM_INFO协议
- 支持JSON配置和向后兼容参数
- 模块化设计，便于扩展和维护
- 通过OperationRegistry统一注册和管理

## 核心功能模块

## 总结

SpotLight 混合驱动服务采用了分层架构设计，通过抽象接口和模块化组件实现了高内聚、低耦合的系统架构。主要特点包括：

1. **可扩展性**: 支持多种WebDriver实现和操作类型
2. **可维护性**: 清晰的模块划分和接口设计
3. **可测试性**: 完善的单元测试和集成测试
4. **高性能**: 连接池管理和资源优化
5. **高可用**: 异常处理和自动恢复机制
6. **混合驱动**: 支持Selenium和Appium两种WebDriver实现

### 最新架构改进 (2024年)

#### 执行器工厂模式
- **统一管理**: 通过 `ExecutorFactory` 统一管理所有执行器类型
- **动态选择**: 支持运行时动态选择执行器类型（selenium/appium）
- **类型安全**: 统一的 `WebExecutor` 接口，确保类型安全
- **向后兼容**: 保持现有 API 兼容性，支持渐进式升级

#### 代码清理和优化
- **移除冗余**: 清理了 `web_driver_decorator` 相关代码
- **统一接口**: 所有业务代码统一通过 `WebExecutor` 接口调用
- **类型修复**: 修复了类型注解不一致的问题
- **架构简化**: 简化了执行器创建和管理流程

#### 使用示例
```python
# 使用工厂模式创建设备（推荐）
device = AndroidDevice(serial_id, executor_type="selenium")
device = AndroidDevice(serial_id, executor_type="appium", 
                      appium_server_url="http://localhost:4723")

# 直接使用工厂创建执行器
executor = executor_factory.get_executor("selenium")
executor = executor_factory.get_executor("appium", 
                                       appium_server_url="http://localhost:4723")
```

这种架构设计为系统的长期维护和功能扩展提供了良好的基础，特别是在支持不同类型的Android应用操作方面具有很大的灵活性。通过工厂模式的引入，系统变得更加模块化和可扩展。 