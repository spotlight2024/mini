# ChromeDriver 节点部署指南

基于 `appium-docker-android` 项目构建的专用 ChromeDriver 节点，支持桌面 Chrome 和 Android WebView 测试。

## 📋 功能特性

### 🚀 核心功能
- **纯 ChromeDriver 节点**: 专注于 ChromeDriver 功能，不包含 Chrome 浏览器
- **Android WebView 测试**: 支持 Android 设备上的 Chrome 应用和 WebView 测试
- **远程 Chrome 连接**: 支持连接到远程 Chrome 实例进行自动化测试
- **ADB 远程连接**: 支持通过网络连接远程 Android 设备
- **Selenium Grid 集成**: 完全兼容 Selenium Grid 4.x
- **轻量化部署**: 基于 Docker 的精简容器方案

### 🔧 技术栈
- **基础镜像**: selenium/node-base:4.33.0-20250606
- **ChromeDriver**: 版本 128.0.6613.0 (纯驱动，无浏览器)
- **ADB**: Android Debug Bridge 支持
- **Xvfb**: 虚拟显示服务器 (按需启用)
- **网络连接**: 支持远程 Chrome 和 Android 设备

## 🛠️ 部署说明

### 1. 快速启动

```bash
# 进入项目目录
cd /root/workspace/mini/docker

# 启动完整的测试环境
docker-compose up -d

# 仅启动 ChromeDriver 节点
docker-compose up -d selenium-hub chromedriver-node
```

### 2. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 查看节点日志
docker-compose logs chromedriver-node

# 访问 Selenium Grid 控制台
# 浏览器打开: http://localhost:4444
```

### 3. 运行测试

```bash
# 安装 Python 依赖
pip install selenium requests

# 运行功能测试
python chromedriver-test.py
```

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SELENIUM_HUB_HOST` | selenium-hub | Selenium Hub 主机地址 |
| `SELENIUM_HUB_PORT` | 4444 | Selenium Hub 端口 |
| `NODE_PORT` | 4444 | 节点服务端口 |
| `MAX_SESSIONS` | 3 | 最大并发会话数 |
| `HEADLESS` | true | 是否启用无头模式 |
| `ENABLE_ADB` | true | 是否启用 ADB 功能 |
| `REMOTE_ADB` | false | 是否使用远程 ADB 连接 |
| `ANDROID_DEVICES` | - | 远程设备列表 (如: 192.168.1.100:5555) |
| `REMOTE_ADB_POLLING_SEC` | 60 | 设备重连检查间隔 |

### Android 设备连接配置

#### USB 连接模式
```yaml
# docker-compose.yml 中启用 USB 设备访问
chromedriver-node:
  privileged: true
  volumes:
    - /dev/bus/usb:/dev/bus/usb
    - ~/.android:/home/seluser/.android:ro
```

#### 无线连接模式
```yaml
# docker-compose.yml 中配置远程设备
chromedriver-node:
  environment:
    - REMOTE_ADB=true
    - ANDROID_DEVICES=192.168.1.100:5555,192.168.1.101:5555
    - REMOTE_ADB_POLLING_SEC=60
```

## 💻 使用示例

### 远程 Chrome 实例测试

```python
from selenium import webdriver

# 连接到远程 Chrome 实例 (需要先启动 Chrome 并开启调试端口)
# chrome --remote-debugging-port=9222 --no-sandbox
capabilities = {
    "browserName": "chrome",
    "platformName": "any", 
    "browserVersion": "128.0",
    "goog:chromeOptions": {
        "debuggerAddress": "host.docker.internal:9222",
        "args": ["--no-sandbox", "--disable-dev-shm-usage"]
    }
}

driver = webdriver.Remote(
    command_executor="http://localhost:4444/wd/hub",
    desired_capabilities=capabilities
)

driver.get("https://www.google.com")
print(driver.title)
driver.quit()
```

### Android WebView 测试

```python
from selenium import webdriver

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

driver = webdriver.Remote(
    command_executor="http://localhost:4444/wd/hub",
    desired_capabilities=capabilities
)

driver.get("https://m.baidu.com")
print(driver.title)
driver.quit()
```

## 🔍 故障排查

### 常见问题

#### 1. 节点无法连接到 Hub
```bash
# 检查网络连接
docker exec chromedriver-node curl -I http://selenium-hub:4444/status

# 检查容器间网络
docker network ls
docker network inspect mini_selenium-grid
```

#### 2. ChromeDriver 功能验证
```bash
# 查看 ChromeDriver 版本和功能
docker exec chromedriver-node /opt/chromedriver/chromedriver --version
docker exec chromedriver-node /opt/chromedriver/chromedriver --help
```

#### 3. Android 设备连接失败
```bash
# 检查 ADB 连接
docker exec chromedriver-node adb devices

# 测试设备连接
docker exec chromedriver-node adb connect <device-ip>:5555
```

#### 4. 权限问题
```bash
# 检查文件权限
docker exec chromedriver-node ls -la /opt/chromedriver/
docker exec chromedriver-node ls -la /home/seluser/.android/
```

### 日志查看

```bash
# 查看详细启动日志
docker-compose logs -f chromedriver-node

# 查看 Selenium Grid 状态
curl http://localhost:4444/status | jq

# 检查节点注册情况
curl http://localhost:4444/status | jq '.value.nodes[].slots'
```

## 📁 文件结构

```
mini/docker/
├── Dockerfile.chromedriver-node      # ChromeDriver 节点镜像定义
├── chromedriver-node.toml           # 节点配置文件
├── chromedriver-entrypoint.sh       # 节点启动脚本
├── chromedriver-test.py             # 功能测试脚本
├── docker-compose.yml               # Docker Compose 配置
└── CHROMEDRIVER_README.md           # 本文档
```

## 🔧 高级配置

### 自定义 ChromeDriver 版本

修改 `Dockerfile.chromedriver-node` 中的版本号：
```dockerfile
ENV CHROMEDRIVER_VERSION=128.0.6613.0
```

### 调整并发会话数

修改 `chromedriver-node.toml` 中的配置：
```toml
max-sessions = 5  # 全局最大会话数

[[node.driver-configuration]]
max-sessions = 3  # 单个驱动最大会话数
```

### 集成到 CI/CD

```yaml
# .github/workflows/test.yml
- name: Start Test Environment
  run: |
    cd mini/docker
    docker-compose up -d selenium-hub chromedriver-node
    
- name: Wait for Grid Ready
  run: |
    timeout 60 bash -c 'until curl -s http://localhost:4444/status; do sleep 2; done'
    
- name: Run Tests
  run: python mini/docker/chromedriver-test.py
```

## 📞 技术支持

如有问题或需要进一步定制，请提供以下信息：
1. 容器运行日志
2. 测试用例和错误信息
3. 设备连接状态
4. 网络配置详情

---

*基于 appium-docker-android 项目构建 | 适用于企业级自动化测试环境* 