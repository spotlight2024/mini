# ConnectConfig 使用指南

## 概述

`ConnectConfig` 是一个统一的数据传输对象，用于在设备连接链路中传递配置参数，从 API 请求一直传递到 WebDriver 连接层。

## 数据流链路

```
ConnectRequest (API层)
    ↓ 转换为
ConnectConfig (配置对象)
    ↓ 传递到
DevicePool.connect()
    ↓ 传递到
AndroidDevice.connect()
    ↓ 传递到
SeleniumWebExecutor.connect()
    ↓ 使用配置
connect_webdriver_with_config()
```

## ConnectConfig 字段说明

```python
class ConnectConfig(BaseModel):
    serial_id: str                    # 设备序列号
    user_id: str                      # 用户ID
    ip: Optional[str] = None          # 设备IP地址
    port: Optional[int] = None        # 设备端口
    executor_type: str = "selenium"   # 执行器类型
    timeout: int = 30                 # 连接超时时间
    webdriver_mode: str = "remote"    # WebDriver模式
    remote_url: Optional[str] = None  # 远程WebDriver地址
    browser_version: Optional[str] = None  # 浏览器版本
    platform_name: Optional[str] = "android"  # 平台名称
    android_package: Optional[str] = "com.tencent.mm"  # Android包名
    android_process: Optional[str] = "com.tencent.mm:appbrand0"  # Android进程名
```

## 使用示例

### 1. API 层使用

```python
@router.post("/connect", response_model=APIResponse)
async def connect(req: ConnectRequest):
    """连接设备"""
    try:
        # 将 ConnectRequest 转换为 ConnectConfig
        config = ConnectConfig(
            serial_id=req.serial_id,
            user_id=req.user_id,
            # 可以添加更多配置参数
            webdriver_mode="remote",
            remote_url="http://172.16.1.129:4444/wd/hub",
            browser_version="138",
            android_package="com.tencent.mm",
            android_process="com.tencent.mm:appbrand0"
        )
        
        device = await run_sync_typed(DevicePool().connect, config)
        # ... 后续处理
```

### 2. DevicePool 层使用

```python
def connect(self, config: ConnectConfig) -> AndroidDevice:
    """连接设备并返回设备实例"""
    with self.lock:
        logging.info(f"[DevicePool] 尝试连接 config={config.model_dump()}")
        device = self.pool.get(config.serial_id)

        if device is None or not device.is_connected():
            try:
                # 使用配置中的执行器类型创建设备
                device = AndroidDevice(
                    serial_id=config.serial_id, 
                    executor_type=config.executor_type
                )
                if device.connect(config):  # 传递完整配置
                    self.pool[config.serial_id] = device
                    logging.info(f"[DevicePool] 设备连接成功 serial_id={config.serial_id}")
                else:
                    raise RuntimeError(f"Failed to connect device: {config.serial_id}")
            except Exception as e:
                logging.error(f"[DevicePool] 设备连接失败 serial_id={config.serial_id}: {e}")
                raise

        return device
```

### 3. AndroidDevice 层使用

```python
def connect(self, config: Optional[ConnectConfig] = None, **kwargs) -> bool:
    """连接设备"""
    try:
        # 初始化 WebExecutor
        if self._web_execute_cls is not None:
            self._web_execute = self._web_execute_cls()
        else:
            self._web_execute = executor_factory.get_executor(
                self._executor_type,
                **self._executor_kwargs
            )

        # 如果提供了 ConnectConfig，使用它；否则使用 kwargs
        if config:
            if not self._web_execute.connect(config):  # 传递配置对象
                logger.error(f"WebExecutor 初始化失败 serial_id={self._serial_id}")
                self._status = "disconnected"
                return False
        else:
            if not self._web_execute.connect(self._serial_id, **kwargs):
                logger.error(f"WebExecutor 初始化失败 serial_id={self._serial_id}")
                self._status = "disconnected"
                return False

        self._status = "connected"
        return True
    except Exception as e:
        logger.exception(f"连接设备 serial_id={self._serial_id} 发生异常: {e}")
        self._status = "disconnected"
        return False
```

### 4. SeleniumWebExecutor 层使用

```python
def connect(self, device_id_or_config: Union[str, ConnectConfig], **kwargs) -> bool:
    """连接到设备"""
    try:
        if isinstance(device_id_or_config, ConnectConfig):
            # 使用 ConnectConfig
            config = device_id_or_config
            self._driver = connect_webdriver_with_config(config)  # 使用配置创建WebDriver
            self._device_id = config.serial_id
            logger.info(f"设备连接成功 serial_id={config.serial_id}")
        else:
            # 向后兼容：使用字符串
            serial_id = device_id_or_config
            self._driver = connect_webdriver(serial_id)
            self._device_id = serial_id
            logger.info(f"设备连接成功 serial_id={serial_id}")
        return True
    except Exception as e:
        logger.error(f"设备连接失败: {e}")
        return False
```

### 5. WebDriver 创建层使用

```python
def connect_webdriver_with_config(config: ConnectConfig) -> WebDriver:
    """使用 ConnectConfig 创建 WebDriver"""
    logger.info(f"开始创建 WebDriver config={config.model_dump()}")
    options = ChromeOptions()

    # 使用配置中的参数
    options.enable_mobile(
        android_package=config.android_package,
        device_serial=config.serial_id,
    )
    options.add_experimental_option("androidUseRunningApp", True)
    if config.android_process:
        options.add_experimental_option("androidProcess", config.android_process)

    options.set_capability("browserName", "chrome")
    
    # 设置浏览器版本和平台
    if config.browser_version:
        options.set_capability("browserVersion", config.browser_version)
    if config.platform_name:
        options.set_capability("platformName", config.platform_name)

    if config.webdriver_mode == "remote":
        # 远程 WebDriver
        remote_url = config.remote_url or settings.REMOTE_WEBDRIVER_URL
        if not remote_url:
            raise ValueError("REMOTE_WEBDRIVER_URL 未配置")
        
        driver = webdriver.Remote(
            command_executor=remote_url,
            options=options
        )
        driver.implicitly_wait(3)
        return driver
    else:
        # 本地 WebDriver
        path = ChromeDriverManager(driver_version=config.browser_version or TEST_CONFIG["chrome_version"]).install()
        service = ChromeService(executable_path=path)
        driver = webdriver.Chrome(options=options, service=service)
        driver.implicitly_wait(3)
        return driver
```

## 配置参数传递示例

### 1. 基本连接配置

```python
config = ConnectConfig(
    serial_id="172.16.1.125:6524",
    user_id="user123"
)
```

### 2. 远程 WebDriver 配置

```python
config = ConnectConfig(
    serial_id="172.16.1.125:6524",
    user_id="user123",
    webdriver_mode="remote",
    remote_url="http://172.16.1.129:4444/wd/hub",
    browser_version="138",
    platform_name="linux"
)
```

### 3. 微信小程序配置

```python
config = ConnectConfig(
    serial_id="172.16.1.125:6524",
    user_id="user123",
    android_package="com.tencent.mm",
    android_process="com.tencent.mm:appbrand0",
    webdriver_mode="remote",
    remote_url="http://172.16.1.129:4444/wd/hub"
)
```

### 4. 自定义应用配置

```python
config = ConnectConfig(
    serial_id="172.16.1.125:6524",
    user_id="user123",
    android_package="com.example.app",
    android_process="com.example.app:main",
    browser_version="134",
    timeout=60
)
```

## 向后兼容性

为了保持向后兼容性，系统提供了以下机制：

### 1. DevicePool 兼容方法

```python
def connect_legacy(self, serial_id, ip=None, port=None) -> AndroidDevice:
    """向后兼容的连接方法"""
    config = ConnectConfig(
        serial_id=serial_id,
        user_id="legacy_user",  # 默认用户ID
        ip=ip,
        port=port
    )
    return self.connect(config)
```

### 2. AndroidDevice 兼容方法

```python
def connect(self, config: Optional[ConnectConfig] = None, **kwargs) -> bool:
    # 如果提供了 ConnectConfig，使用它；否则使用 kwargs
    if config:
        # 使用新的配置方式
        pass
    else:
        # 使用传统的 kwargs 方式
        pass
```

### 3. SeleniumWebExecutor 兼容方法

```python
def connect(self, device_id_or_config: Union[str, ConnectConfig], **kwargs) -> bool:
    if isinstance(device_id_or_config, ConnectConfig):
        # 使用新的配置方式
        pass
    else:
        # 使用传统的字符串方式
        pass
```

## 优势

### 1. 类型安全
- 使用 Pydantic 模型提供类型检查和验证
- 编译时发现类型错误

### 2. 参数完整性
- 所有连接参数在一个对象中管理
- 避免参数在传递过程中丢失

### 3. 易于扩展
- 添加新参数只需修改 ConnectConfig 模型
- 不影响现有代码

### 4. 统一配置
- 所有连接相关的配置集中管理
- 便于调试和监控

### 5. 向后兼容
- 保持现有代码的兼容性
- 渐进式迁移

## 最佳实践

### 1. 配置验证
```python
# 在 API 层验证配置
config = ConnectConfig(
    serial_id=req.serial_id,
    user_id=req.user_id
)
# Pydantic 会自动验证字段类型和约束
```

### 2. 日志记录
```python
# 记录配置信息用于调试
logger.info(f"连接配置: {config.model_dump()}")
```

### 3. 错误处理
```python
try:
    device = await run_sync_typed(DevicePool().connect, config)
except Exception as e:
    logger.error(f"连接失败 config={config.model_dump()}, error={e}")
    raise
```

### 4. 配置复用
```python
# 可以创建配置模板
DEFAULT_CONFIG = ConnectConfig(
    executor_type="selenium",
    webdriver_mode="remote",
    timeout=30
)

# 使用时合并配置
config = DEFAULT_CONFIG.model_copy(update={
    "serial_id": req.serial_id,
    "user_id": req.user_id
})
```

## 总结

使用 `ConnectConfig` 实现了：

1. **完整的数据传递链路**：从 API 请求到 WebDriver 连接
2. **类型安全的配置管理**：使用 Pydantic 模型
3. **灵活的配置选项**：支持各种连接参数
4. **向后兼容性**：保持现有代码可用
5. **易于维护和扩展**：统一的配置管理

这种方式比传统的参数传递更加优雅、安全和可维护。 