# ADB Session Factory - Selenium Grid SPI扩展

这是一个Selenium Grid的SPI（Service Provider Interface）扩展，用于在创建WebDriver会话前自动连接ADB设备。

## 功能特性

- 自动检测包含`se:adbDeviceId`能力的Chrome会话请求
- 在创建会话前自动执行`adb connect`命令
- 支持装饰器模式，委托给原生SessionFactory
- 完整的日志记录和错误处理

## 构建

```bash
mvn clean package
```

## 使用方法

### 方法一：通过--ext参数加载（推荐）

```bash
# 启动Selenium Grid Node时加载扩展jar包
java -jar selenium-server.jar node --ext /path/to/adb-session-factory.jar
```

### 方法二：通过配置文件指定

在Selenium Grid配置文件（如`config.toml`）中添加：

```toml
[node]
driver-factories = [
  "com.spotlight.adb.AdbSessionFactory",
  '{"browserName": "chrome", "se:adbDeviceId": "required"}'
]
```

### 方法三：通过环境变量

```bash
export SELENIUM_NODE_DRIVER_FACTORIES="com.spotlight.adb.AdbSessionFactory"
java -jar selenium-server.jar node
```

## 客户端使用示例

### Java客户端

```java
ChromeOptions options = new ChromeOptions();
options.setCapability("se:adbDeviceId", "192.168.1.100:5555");

WebDriver driver = new RemoteWebDriver(new URL("http://localhost:4444"), options);
```

### Python客户端

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.set_capability("se:adbDeviceId", "192.168.1.100:5555")

driver = webdriver.Remote(
    command_executor='http://localhost:4444',
    options=options
)
```

### JavaScript客户端

```javascript
const {Builder} = require('selenium-webdriver');

let driver = await new Builder()
    .forBrowser('chrome')
    .usingServer('http://localhost:4444')
    .withCapabilities({
        'se:adbDeviceId': '192.168.1.100:5555'
    })
    .build();
```

## 工作原理

1. **会话匹配**：当收到包含`se:adbDeviceId`能力的Chrome会话请求时，此工厂会被选中
2. **ADB连接**：在创建会话前，自动执行`adb connect {deviceId}`命令
3. **会话创建**：委托给原生SessionFactory创建实际的WebDriver会话
4. **错误处理**：如果ADB连接失败，会抛出WebDriverException

## 配置选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `se:adbDeviceId` | ADB设备ID（IP:端口或设备序列号） | 必需 |

## 日志

扩展会输出详细的日志信息，包括：
- 会话匹配过程
- ADB连接命令执行
- 错误和异常信息

日志级别可以通过JVM参数调整：
```bash
-Djava.util.logging.config.file=logging.properties
```

## 故障排除

### 常见问题

1. **ADB命令未找到**
   - 确保ADB已安装并添加到PATH环境变量
   - 在Linux/Mac上：`export PATH=$PATH:/path/to/android-sdk/platform-tools`

2. **设备连接失败**
   - 检查设备IP地址和端口是否正确
   - 确保设备已启用USB调试和网络调试
   - 检查防火墙设置

3. **SPI加载失败**
   - 确保jar包路径正确
   - 检查META-INF/services文件是否存在
   - 验证类名是否正确

### 调试模式

启用详细日志：
```bash
java -Djava.util.logging.ConsoleHandler.level=FINE -jar selenium-server.jar node --ext adb-session-factory.jar
```

## 开发说明

### 项目结构

```
src/
├── main/
│   ├── java/
│   │   └── com/spotlight/adb/
│   │       └── AdbSessionFactory.java
│   └── resources/
│       └── META-INF/
│           └── services/
│               └── org.openqa.selenium.grid.node.SessionFactory
```

### SPI接口要求

- 实现`SessionFactory`接口
- 提供静态`create(Config, Capabilities)`方法
- 在`META-INF/services`中注册

### 扩展点

- `test(Capabilities)`：决定是否处理特定会话请求
- `apply(CreateSessionRequest)`：执行ADB连接和会话创建
- `getStereotype()`：返回支持的能力配置

## 许可证

Apache License 2.0 