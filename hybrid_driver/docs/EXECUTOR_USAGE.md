# 执行器使用指南

## 概述

本项目支持多种自动化执行器，包括 Selenium（Web 自动化）和 Appium（移动端自动化）。通过统一的接口和工厂模式，可以灵活切换不同的执行器而不影响业务代码。

## 支持的执行器

### 1. SeleniumWebExecutor
- **用途**: Web 自动化，特别适用于微信小程序 WebView
- **特点**: 基于 Selenium WebDriver，支持 Chrome 浏览器
- **适用场景**: Web 页面操作、小程序自动化

### 2. AppiumExecutor  
- **用途**: 移动端自动化，支持原生 Android 应用
- **特点**: 基于 Appium，支持 UiAutomator2
- **适用场景**: 原生应用操作、混合应用自动化

## 使用方式

### 方式一：向后兼容（推荐）

保持原有代码不变，默认使用 Selenium：

```python
from hybrid_driver.device.android_device import AndroidDevice

# 默认使用 SeleniumWebExecutor
device = AndroidDevice(serial_id="your_device_id")
device.connect()
```

### 方式二：指定执行器类型

```python
from hybrid_driver.device.android_device import AndroidDevice

# 使用 Selenium
device = AndroidDevice(
    serial_id="your_device_id",
    executor_type="selenium"
)

# 使用 Appium
device = AndroidDevice(
    serial_id="your_device_id", 
    executor_type="appium",
    appium_server_url="http://localhost:4723",
    capabilities={
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:appPackage": "com.tencent.mm",
        "appium:appActivity": "com.tencent.mm/.plugin.appbrand.ui.AppBrandUI00"
    }
)
```

### 方式三：直接传入执行器类（完全向后兼容）

```python
from hybrid_driver.device.android_device import AndroidDevice
from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor
from hybrid_driver.webdriver.appium_executor import AppiumExecutor

# 使用 Selenium
device = AndroidDevice(
    serial_id="your_device_id",
    web_execute_cls=SeleniumWebExecutor
)

# 使用 Appium
device = AndroidDevice(
    serial_id="your_device_id",
    web_execute_cls=lambda: AppiumExecutor(
        appium_server_url="http://localhost:4723",
        capabilities={...}
    )
)
```

## 业务代码示例

无论使用哪种执行器，业务代码都保持一致：

```python
# 连接设备
device = AndroidDevice(serial_id="your_device_id", executor_type="selenium")
device.connect()

# 查找元素
element = device.find_element("id", "login_button")

# 点击操作
if element:
    element.click()

# 等待新窗口
device.wait_for_new_window()

# 获取页面信息
url = device.get_current_url()
page_source = device.get_page_source()

# 执行脚本
result = device.execute_script("return document.title")

# 断开连接
device.disconnect()
```

## 工厂模式扩展

### 注册新的执行器

```python
from hybrid_driver.webdriver.executor_factory import executor_factory
from hybrid_driver.webdriver.web_executor import WebExecutor

class CustomExecutor(WebExecutor):
    def connect(self, device_id: str, **kwargs) -> bool:
        # 实现连接逻辑
        pass
    
    def quit(self) -> None:
        # 实现断开逻辑
        pass
    
    # ... 实现其他抽象方法

# 注册新的执行器
executor_factory.register_executor("custom", CustomExecutor)

# 使用新的执行器
device = AndroidDevice(
    serial_id="your_device_id",
    executor_type="custom"
)
```

### 获取可用执行器列表

```python
from hybrid_driver.webdriver.executor_factory import executor_factory

available_executors = executor_factory.get_available_executors()
print(f"可用执行器: {available_executors}")
# 输出: ['selenium', 'appium']
```

## 配置建议

### 开发环境
```python
# 使用 Selenium，便于调试
device = AndroidDevice(
    serial_id="your_device_id",
    executor_type="selenium"
)
```

### 生产环境
```python
# 根据实际需求选择执行器
device = AndroidDevice(
    serial_id="your_device_id",
    executor_type="appium",  # 或 "selenium"
    appium_server_url="http://appium-server:4723",
    capabilities={
        "platformName": "Android",
        "appium:automationName": "UiAutomator2"
    }
)
```

## 注意事项

1. **向后兼容**: 现有代码无需修改，默认使用 Selenium
2. **类型安全**: 所有执行器都实现相同的接口，确保类型安全
3. **错误处理**: 统一的错误处理机制，便于调试和维护
4. **资源管理**: 使用上下文管理器自动管理资源

```python
# 推荐使用上下文管理器
with AndroidDevice(serial_id="your_device_id") as device:
    # 执行操作
    element = device.find_element("id", "button")
    if element:
        element.click()
```

## 故障排除

### 常见问题

1. **执行器连接失败**
   - 检查设备 ID 是否正确
   - 确认执行器服务是否启动
   - 查看日志获取详细错误信息

2. **元素查找失败**
   - 确认元素定位方式是否正确
   - 检查页面是否完全加载
   - 尝试增加等待时间

3. **类型错误**
   - 确保使用正确的执行器类型
   - 检查参数格式是否正确

### 调试技巧

```python
import logging
from hybrid_driver.log_config import setup_logging

# 启用详细日志
setup_logging(level=logging.DEBUG)

# 创建设备并查看连接过程
device = AndroidDevice(serial_id="your_device_id", executor_type="selenium")
success = device.connect()
print(f"连接结果: {success}")
``` 