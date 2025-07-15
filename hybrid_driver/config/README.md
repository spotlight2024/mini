# SpotLight 配置管理

## 概述

SpotLight 使用统一的配置管理系统，支持从环境变量、配置文件、默认值等多种方式读取配置。

## 配置来源优先级

1. **环境变量** (最高优先级)
2. **配置文件** (`config/config.json`)
3. **默认值** (最低优先级)

## 配置项分类

### API服务配置
- `API_HOST`: API服务主机地址
- `API_PORT`: API服务端口
- `API_RELOAD`: 是否启用热重载
- `API_WORKERS`: 工作进程数
- `API_TITLE`: API标题
- `API_DESCRIPTION`: API描述
- `API_VERSION`: API版本

### 日志配置
- `LOG_LEVEL`: 日志级别 (DEBUG, INFO, WARNING, ERROR)
- `LOG_FORMAT`: 日志格式
- `LOG_FILE`: 日志文件路径
- `LOG_MAX_SIZE`: 日志文件最大大小
- `LOG_BACKUP_COUNT`: 日志备份数量
- `LOG_ENABLE_CONSOLE`: 是否启用控制台日志
- `LOG_ENABLE_FILE`: 是否启用文件日志

### WebDriver配置
- `SELENIUM_TIMEOUT`: Selenium超时时间
- `APPIUM_TIMEOUT`: Appium超时时间
- `CHROME_DRIVER_PATH`: ChromeDriver路径
- `CHROME_DRIVER_VERSION`: ChromeDriver版本
- `CHROME_DRIVER_DOWNLOAD_URL`: ChromeDriver下载URL
- `APPIUM_SERVER_URL`: Appium服务器URL
- `WEBDRIVER_MODE`: WebDriver模式 (local/remote)
- `REMOTE_WEBDRIVER_URL`: 远程WebDriver URL

### Selenium Grid配置
- `SELENIUM_HUB_HOST`: Selenium Hub主机
- `SELENIUM_HUB_PUBLISH_PORT`: Selenium Hub发布端口
- `SELENIUM_HUB_SUBSCRIBE_PORT`: Selenium Hub订阅端口
- `SELENIUM_NODE_COUNT`: Selenium节点数量
- `SELENIUM_NODE_MAX_SESSIONS`: 节点最大会话数
- `SELENIUM_NODE_SESSION_TIMEOUT`: 节点会话超时时间

### 设备池配置
- `MAX_DEVICES`: 最大设备数量
- `CLEANUP_INTERVAL`: 清理间隔时间
- `DEVICE_TIMEOUT`: 设备超时时间
- `DEVICE_CONNECTION_RETRY`: 设备连接重试次数
- `DEVICE_CONNECTION_RETRY_DELAY`: 设备连接重试延迟

### 操作配置
- `DEFAULT_TIMEOUT`: 默认超时时间
- `DEFAULT_WAIT`: 默认等待时间
- `ELEMENT_WAIT_TIMEOUT`: 元素等待超时时间
- `PAGE_LOAD_TIMEOUT`: 页面加载超时时间
- `SCRIPT_TIMEOUT`: 脚本执行超时时间

### 线程池配置
- `THREAD_POOL_MAX_WORKERS`: 最大工作线程数
- `THREAD_POOL_MIN_WORKERS`: 最小工作线程数

### 连接池配置
- `CONNECTION_POOL_MAX_CONNECTIONS`: 最大连接数
- `CONNECTION_POOL_MAX_IDLE_TIME`: 最大空闲时间

### 网络配置
- `NETWORK_NAME`: 网络名称
- `NETWORK_TIMEOUT`: 网络超时时间

### 证书配置
- `SE_INSTALL_CERTIFICATES`: 是否安装证书

### 缓存配置
- `CACHE_ENABLED`: 是否启用缓存
- `CACHE_TTL`: 缓存生存时间
- `CACHE_MAX_SIZE`: 缓存最大大小

### 监控配置
- `METRICS_ENABLED`: 是否启用指标收集
- `METRICS_INTERVAL`: 指标收集间隔
- `AUTO_SCALE_ENABLED`: 是否启用自动扩缩容

### 安全配置
- `CORS_ENABLED`: 是否启用CORS
- `CORS_ORIGINS`: CORS允许的源
- `API_KEY_ENABLED`: 是否启用API密钥
- `API_KEY_HEADER`: API密钥请求头

## 使用方法

### 1. 在代码中使用配置

```python
from hybrid_driver.config.settings import settings

# 获取API配置
api_host = settings.API_HOST
api_port = settings.API_PORT

# 获取WebDriver配置
selenium_timeout = settings.SELENIUM_TIMEOUT
webdriver_mode = settings.WEBDRIVER_MODE

# 获取线程池配置
max_workers = settings.THREAD_POOL_MAX_WORKERS
```

### 2. 使用配置管理工具

```bash
# 显示当前配置
python hybrid_driver/config_manager.py show

# 导出配置到文件
python hybrid_driver/config_manager.py export -o config_export.json

# 从文件导入配置
python hybrid_driver/config_manager.py import -f config_export.json

# 验证配置
python hybrid_driver/config_manager.py validate

# 创建环境变量文件
python hybrid_driver/config_manager.py create-env -o .env

# 创建配置模板
python hybrid_driver/config_manager.py create-template

# 显示配置来源
python hybrid_driver/config_manager.py sources
```

### 3. 环境变量配置

创建 `.env` 文件：

```bash
# API服务配置
API_HOST=0.0.0.0
API_PORT=8002
API_RELOAD=true

# 日志配置
LOG_LEVEL=INFO
LOG_ENABLE_CONSOLE=true
LOG_ENABLE_FILE=true

# WebDriver配置
SELENIUM_TIMEOUT=30
WEBDRIVER_MODE=local

# 线程池配置
THREAD_POOL_MAX_WORKERS=100
```

### 4. 配置文件配置

创建 `config/config.json` 文件：

```json
{
  "api": {
    "host": "0.0.0.0",
    "port": 8002,
    "reload": true
  },
  "logging": {
    "level": "INFO",
    "enable_console": true,
    "enable_file": true
  },
  "webdriver": {
    "selenium_timeout": 30,
    "webdriver_mode": "local"
  },
  "thread_pool": {
    "max_workers": 100
  }
}
```

## 配置验证

配置系统会自动验证配置项的有效性：

- 端口范围检查 (1-65535)
- 超时时间检查 (> 0)
- 线程池配置检查 (max >= min)
- WebDriver模式检查 (local/remote)

## 最佳实践

### 1. 开发环境
- 使用 `.env` 文件进行本地配置
- 启用详细日志和热重载
- 使用本地WebDriver模式

### 2. 生产环境
- 使用环境变量进行配置
- 禁用热重载和详细日志
- 使用远程WebDriver模式
- 启用监控和自动扩缩容

### 3. 测试环境
- 使用配置文件进行配置
- 启用指标收集
- 使用较小的线程池大小

## 常见问题

### Q: 如何修改线程池大小？
A: 设置环境变量 `THREAD_POOL_MAX_WORKERS` 或在配置文件中修改。

### Q: 如何切换WebDriver模式？
A: 设置环境变量 `WEBDRIVER_MODE=remote` 并配置 `REMOTE_WEBDRIVER_URL`。

### Q: 如何启用详细日志？
A: 设置环境变量 `LOG_LEVEL=DEBUG` 和 `LOG_ENABLE_CONSOLE=true`。

### Q: 配置修改后需要重启吗？
A: 环境变量修改需要重启，配置文件修改可以通过热重载生效（如果启用）。

## 配置示例

### 开发环境配置
```bash
# .env
API_PORT=8002
LOG_LEVEL=DEBUG
WEBDRIVER_MODE=local
API_RELOAD=true
THREAD_POOL_MAX_WORKERS=50
```

### 生产环境配置
```bash
# 环境变量
export API_PORT=8000
export LOG_LEVEL=INFO
export WEBDRIVER_MODE=remote
export REMOTE_WEBDRIVER_URL=http://selenium-hub:4444
export THREAD_POOL_MAX_WORKERS=200
export METRICS_ENABLED=true
export AUTO_SCALE_ENABLED=true
```

### 测试环境配置
```json
{
  "api": {
    "port": 8001
  },
  "logging": {
    "level": "WARNING"
  },
  "webdriver": {
    "webdriver_mode": "local"
  },
  "thread_pool": {
    "max_workers": 20
  },
  "monitoring": {
    "metrics_enabled": true
  }
}
``` 