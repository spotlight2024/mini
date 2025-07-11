# ChromeDriver 纯节点使用指南

## 🎯 节点特性

本 ChromeDriver 节点是一个**纯驱动节点**，具有以下特点：

### ✅ 包含的功能
- ✅ **ChromeDriver 128.0.6613.0** - 完整的 WebDriver 协议支持
- ✅ **ADB 工具** - 连接和管理 Android 设备
- ✅ **Selenium Grid 集成** - 标准的 Grid 4.x 节点
- ✅ **网络连接能力** - 支持远程设备和服务连接

### ❌ 不包含的功能
- ❌ **Chrome 浏览器** - 节点内不安装 Chrome，保持轻量化
- ❌ **桌面 GUI 支持** - 专注于无头和远程连接场景
- ❌ **X11 转发** - 除非明确需要，否则默认关闭

## 🚀 主要用例

### 1. Android WebView 自动化
```python
from selenium import webdriver

# Android WebView 测试
capabilities = {
    "browserName": "chrome",
    "platformName": "android",
    "browserVersion": "128.0",
    "appium:automationName": "UiAutomator2",
    "appium:chromeOptions": {
        "androidPackage": "com.android.chrome",
        "androidUseRunningApp": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"]
    }
}

driver = webdriver.Remote("http://localhost:4444/wd/hub", capabilities)
```

### 2. 远程 Chrome 实例连接
```python
# 先在宿主机启动 Chrome (开启调试端口)
# google-chrome --remote-debugging-port=9222 --no-sandbox --disable-web-security

capabilities = {
    "browserName": "chrome",
    "platformName": "any",
    "browserVersion": "128.0",
    "goog:chromeOptions": {
        "debuggerAddress": "host.docker.internal:9222",
        "args": ["--no-sandbox", "--disable-dev-shm-usage"]
    }
}

driver = webdriver.Remote("http://localhost:4444/wd/hub", capabilities)
```

### 3. 云端 Chrome 服务连接
```python
# 连接到云端 Chrome 服务 (如 Browserless)
capabilities = {
    "browserName": "chrome",
    "platformName": "any",
    "browserVersion": "128.0",
    "goog:chromeOptions": {
        "debuggerAddress": "chrome-service:9222",
        "args": ["--no-sandbox", "--disable-dev-shm-usage"]
    }
}
```

## 🔧 配置选项

### 环境变量
```yaml
chromedriver-node:
  environment:
    # 基础配置
    - SELENIUM_HUB_HOST=selenium-hub
    - SELENIUM_HUB_PORT=4444
    - NODE_PORT=5555
    - MAX_SESSIONS=3
    
    # 显示配置
    - HEADLESS=true              # 默认无头模式
    
    # ADB 配置
    - ENABLE_ADB=true            # 启用 ADB 功能
    - REMOTE_ADB=false           # 是否使用远程 ADB
    - ANDROID_DEVICES=192.168.1.100:5555  # 远程设备列表
    - REMOTE_ADB_POLLING_SEC=60  # 设备重连间隔
```

### 卷挂载配置
```yaml
chromedriver-node:
  volumes:
    # Android 设备授权 (USB 连接时需要)
    - ~/.android:/home/seluser/.android:ro
    
    # USB 设备访问 (物理连接时需要)
    - /dev/bus/usb:/dev/bus/usb
    
    # X11 支持 (GUI 应用调试时需要)
    - /tmp/.X11-unix:/tmp/.X11-unix:rw
```

## 📋 部署场景

### 场景 1: 纯 Android WebView 测试
```yaml
chromedriver-node:
  environment:
    - ENABLE_ADB=true
    - REMOTE_ADB=true
    - ANDROID_DEVICES=192.168.1.100:5555,192.168.1.101:5555
    - HEADLESS=true
  # 不需要额外的卷挂载
```

### 场景 2: 混合测试 (Android + 远程 Chrome)
```yaml
chromedriver-node:
  environment:
    - ENABLE_ADB=true
    - REMOTE_ADB=true
    - ANDROID_DEVICES=192.168.1.100:5555
    - HEADLESS=true
  # Chrome 实例需要在其他地方运行，通过网络连接
```

### 场景 3: USB 连接的 Android 设备
```yaml
chromedriver-node:
  privileged: true
  environment:
    - ENABLE_ADB=true
    - REMOTE_ADB=false
  volumes:
    - /dev/bus/usb:/dev/bus/usb
    - ~/.android:/home/seluser/.android:ro
```

## 🔍 故障排查

### 检查 ChromeDriver 状态
```bash
# 验证 ChromeDriver 可执行
docker exec chromedriver-node /opt/chromedriver/chromedriver --version

# 检查 Grid 注册状态
curl http://localhost:4444/status | jq '.value.nodes[].slots'

# 查看节点详细信息
curl http://localhost:4444/status | jq '.value.nodes[] | {id, uri, slots}'
```

### 检查 Android 连接
```bash
# 查看已连接设备
docker exec chromedriver-node adb devices

# 测试设备连接
docker exec chromedriver-node adb -s DEVICE_ID shell dumpsys window | grep mCurrentFocus
```

### 检查远程 Chrome 连接
```bash
# 测试远程 Chrome 调试端口
curl http://host.docker.internal:9222/json/version

# 列出远程 Chrome 标签页
curl http://host.docker.internal:9222/json
```

## ⚡ 性能优化

### 1. 会话管理
```toml
# chromedriver-node.toml
[node]
max-sessions = 5  # 根据硬件调整

[[node.driver-configuration]]
max-sessions = 3  # 单个驱动最大会话
```

### 2. 网络优化
```yaml
chromedriver-node:
  networks:
    selenium-grid:
      aliases:
        - chrome-node
  # 使用别名提高网络访问性能
```

### 3. 资源限制
```yaml
chromedriver-node:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
      reservations:
        memory: 512M
        cpus: '0.5'
```

## 🎉 最佳实践

### 1. 设备管理
- 使用设备池管理多个 Android 设备
- 定期检查设备连接状态
- 为不同设备配置不同的 capabilities

### 2. 会话管理
- 合理设置会话超时时间
- 及时释放不用的会话
- 监控并发会话数量

### 3. 监控告警
```bash
# 设置健康检查
docker-compose exec chromedriver-node curl -f http://localhost:5555/status

# 监控设备连接
docker-compose exec chromedriver-node adb devices | grep -c "device$"
```

### 4. 日志管理
```bash
# 查看实时日志
docker-compose logs -f chromedriver-node

# 日志轮转配置
docker-compose.yml:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

---

**总结**: 这是一个专门的 ChromeDriver 节点，不包含 Chrome 浏览器，专注于 Android WebView 和远程 Chrome 实例的自动化测试，具有轻量化、高效率的特点。 