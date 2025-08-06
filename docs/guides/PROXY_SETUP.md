# Chrome代理插件使用指南

## 概述

本指南介绍如何在SpotLight项目中使用Chrome代理插件来绕过淘宝等网站的反爬虫检测。该方案通过将Chrome扩展集成到Docker镜像中，在容器启动时通过环境变量动态配置代理，避免Docker层面代理设置导致的鉴权弹框问题。

## 功能特性

- ✅ 自动处理HTTP代理认证，无弹框提示
- ✅ 支持用户名密码认证的代理
- ✅ 代理插件集成到Docker镜像中
- ✅ 通过环境变量动态配置代理
- ✅ 无需修改Python代码即可启用/禁用代理
- ✅ 增强反检测能力
- ✅ 访问淘宝桌面版而非移动版

## 实现原理

### 核心架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Python Client │────│  Selenium Grid   │────│  Chrome + Proxy │
│   (test script) │    │      Hub         │    │    Extension    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                         ┌──────────────────┐    ┌─────────────────┐
                         │  Docker Network  │    │ Proxy Server    │
                         │   (172.18.x.x)   │    │ 61.132.231.167  │
                         └──────────────────┘    └─────────────────┘
```

### 关键技术实现

#### 1. Docker镜像集成
- 基于`selenium/node-chrome:128.0.6613.137`官方镜像
- Chrome扩展文件预置在`/opt/chrome_extensions/proxy_auth/`
- Chrome包装脚本强制加载扩展：`--load-extension=/opt/chrome_extensions/proxy_auth`

#### 2. Chrome包装脚本机制

**包装脚本原理**：
```bash
# 原始Chrome启动
/usr/bin/google-chrome --no-sandbox --disable-dev-shm-usage ...

# 包装脚本处理后
/usr/bin/google-chrome.original --load-extension=/opt/chrome_extensions/proxy_auth --disable-blink-features=AutomationControlled --no-sandbox --disable-dev-shm-usage ...
```

**包装脚本逻辑**：
```bash
#!/bin/bash
EXTENSION_PATH="/opt/chrome_extensions/proxy_auth"
ORIGINAL_CHROME="/usr/bin/google-chrome.original"

if [ "$PROXY_ENABLED" = "true" ] && [ -d "$EXTENSION_PATH" ]; then
    if [[ "$*" != *"--load-extension"* ]]; then
        exec "$ORIGINAL_CHROME" --load-extension="$EXTENSION_PATH" --disable-blink-features=AutomationControlled "$@"
    else
        exec "$ORIGINAL_CHROME" "$@"
    fi
else
    exec "$ORIGINAL_CHROME" "$@"
fi
```

#### 3. 动态代理配置流程

```
容器启动 → custom_startup.sh
    ↓
读取环境变量 → setup_proxy_config.sh  
    ↓
生成proxy_config.json → Chrome扩展读取
    ↓
Chrome启动时自动加载扩展
```

#### 4. Chrome扩展工作原理

**background.js核心逻辑**：
```javascript
// 1. 读取配置文件
async function loadProxyConfig() {
    const response = await fetch(chrome.runtime.getURL('proxy_config.json'));
    const config = await response.json();
    proxyConfig = {
        host: config.host,
        port: config.port,
        username: config.username,
        password: config.password,
        enabled: config.enabled
    };
}

// 2. 设置Chrome代理
function updateProxySettings() {
    const config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: proxyConfig.host,
                port: parseInt(proxyConfig.port)
            }
        }
    };
    chrome.proxy.settings.set({value: config, scope: 'regular'});
}

// 3. 自动认证处理
chrome.webRequest.onAuthRequired.addListener(
    function(details) {
        if (details.isProxy && proxyConfig.enabled && proxyConfig.username && proxyConfig.password) {
            return {
                authCredentials: {
                    username: proxyConfig.username,
                    password: proxyConfig.password
                }
            };
        }
        return {};
    },
    {urls: ["<all_urls>"]},
    ["blocking"]
);
```

#### 5. 反检测机制

- **桌面版User-Agent**：`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36`
- **反自动化参数**：`--disable-blink-features=AutomationControlled`
- **扩展自动认证**：避免弹出认证对话框

## 部署和运行

### 1. 构建镜像

```bash
cd mini/docker
./build_proxy_image.sh
```

**构建过程**：
- 基于官方Selenium Chrome镜像
- 复制Chrome扩展文件到镜像
- 创建Chrome包装脚本
- 备份原始Chrome并替换为包装脚本
- 复制自定义启动脚本

### 2. 代理配置

**环境变量配置** (`mini/docker/proxy.env`)：
```bash
# 启用代理
PROXY_ENABLED=true

# 淘宝反爬虫代理配置
PROXY_HOST=61.132.231.167
PROXY_PORT=57001
PROXY_USERNAME=vgmpgv
PROXY_PASSWORD=1bk79g9y
```

**配置说明**：
| 环境变量 | 说明 | 必需 | 示例值 |
|---------|------|------|--------|
| `PROXY_ENABLED` | 是否启用代理 | 是 | `true` / `false` |
| `PROXY_HOST` | 代理服务器地址 | 是* | `61.132.231.167` |
| `PROXY_PORT` | 代理服务器端口 | 是* | `57001` |
| `PROXY_USERNAME` | 代理用户名 | 否 | `vgmpgv` |
| `PROXY_PASSWORD` | 代理密码 | 否 | `1bk79g9y` |

*当`PROXY_ENABLED=true`时必需

### 3. 启动服务

```bash
# 使用代理配置启动服务
docker compose --env-file proxy.env up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f chrome-driver
```

### 4. 测试验证

```bash
# 测试代理功能
cd ..
python3 scripts/test_web_proxy.py
```

**预期结果**：
- ✅ 代理IP生效（显示代理出口IP）
- ✅ 无认证弹框
- ✅ 访问淘宝桌面版 (`https://www.taobao.com/`)
- ✅ 桌面版User-Agent

### 5. Python代码使用

```python
from hybrid_driver.webdriver.selenium_executor import connect_webdriver_with_config
from hybrid_driver.api.models import ConnectConfig

# 创建连接配置
config = ConnectConfig(
    webdriver_mode="remote",
    remote_url="http://172.16.1.129:4444/wd/hub"
)

# 创建WebDriver（代理通过Docker环境变量自动配置）
driver = connect_webdriver_with_config(config, use_proxy=True)

try:
    # 访问淘宝
    driver.get("https://www.taobao.com")
    print(f"成功访问: {driver.title}")
finally:
    driver.quit()
```

## 文件结构

```
mini/
├── docker/
│   ├── chrome_extensions/proxy_auth/    # Chrome代理扩展
│   │   ├── manifest.json               # 扩展清单
│   │   ├── background.js               # 代理和认证逻辑
│   │   └── config.js                   # 配置注入脚本
│   ├── scripts/
│   │   ├── custom_startup.sh           # 容器启动脚本
│   │   └── setup_proxy_config.sh       # 代理配置生成
│   ├── Dockerfile.custom-selenium-chrome # Docker镜像定义
│   ├── proxy.env                       # 代理环境变量
│   └── build_proxy_image.sh            # 构建脚本
├── scripts/
│   └── test_web_proxy.py               # Web代理测试脚本
└── hybrid_driver/webdriver/
    └── selenium_executor.py            # WebDriver创建逻辑
```

## 技术细节

### Chrome包装脚本实现

**构建时**：
```dockerfile
# 创建Chrome包装脚本
RUN cat > /usr/local/bin/chrome-with-proxy << 'EOF'
#!/bin/bash
# Chrome启动包装脚本，强制加载代理扩展
EXTENSION_PATH="/opt/chrome_extensions/proxy_auth"
ORIGINAL_CHROME="/usr/bin/google-chrome.original"

if [ "$PROXY_ENABLED" = "true" ] && [ -d "$EXTENSION_PATH" ]; then
    if [[ "$*" != *"--load-extension"* ]]; then
        exec "$ORIGINAL_CHROME" --load-extension="$EXTENSION_PATH" --disable-blink-features=AutomationControlled "$@"
    else
        exec "$ORIGINAL_CHROME" "$@"
    fi
else
    exec "$ORIGINAL_CHROME" "$@"
fi
EOF

# 备份原始Chrome并替换为包装脚本
RUN mv /usr/bin/google-chrome /usr/bin/google-chrome.original
RUN ln -s /usr/local/bin/chrome-with-proxy /usr/bin/google-chrome
```

**运行时**：
```bash
# Selenium调用
/usr/bin/google-chrome --no-sandbox --disable-dev-shm-usage ...

# 实际执行
/usr/local/bin/chrome-with-proxy --no-sandbox --disable-dev-shm-usage ...

# 包装脚本处理后
/usr/bin/google-chrome.original --load-extension=/opt/chrome_extensions/proxy_auth --disable-blink-features=AutomationControlled --no-sandbox --disable-dev-shm-usage ...
```

### 代理配置生成

**setup_proxy_config.sh**：
```bash
#!/bin/bash
# 根据环境变量生成代理配置

PROXY_CONFIG_FILE="/opt/chrome_extensions/proxy_auth/proxy_config.json"

if [ "$PROXY_ENABLED" = "true" ]; then
    cat <<EOF > "$PROXY_CONFIG_FILE"
{
  "host": "${PROXY_HOST}",
  "port": "${PROXY_PORT}",
  "username": "${PROXY_USERNAME}",
  "password": "${PROXY_PASSWORD}",
  "enabled": true
}
EOF
    echo "代理配置文件已生成: $PROXY_CONFIG_FILE"
else
    cat <<EOF > "$PROXY_CONFIG_FILE"
{
  "enabled": false
}
EOF
    echo "代理功能未启用"
fi
```

## 故障排除

### 常见问题

1. **代理连接失败**
   - 检查代理服务器地址和端口
   - 确认用户名密码正确
   - 查看Chrome容器日志

2. **插件加载失败**
   - 检查插件文件权限
   - 确保临时目录可写
   - 查看WebDriver创建日志

3. **仍然被反爬虫检测**
   - 尝试更换代理IP
   - 调整访问频率
   - 检查User-Agent设置

4. **访问的是手机版淘宝**
   - 确认User-Agent设置为桌面版
   - 检查Chrome启动参数

### 调试方法

```python
# 启用详细日志
import logging
logging.getLogger('hybrid_driver').setLevel(logging.DEBUG)

# 检查代理状态
driver.get("https://httpbin.org/ip")
print(driver.page_source)  # 查看当前IP
```

### 容器内调试

```bash
# 进入Chrome容器
docker exec -it docker-chrome-driver-1 bash

# 检查扩展文件
ls -la /opt/chrome_extensions/proxy_auth/

# 检查代理配置
cat /opt/chrome_extensions/proxy_auth/proxy_config.json

# 检查Chrome进程
ps aux | grep chrome
```

## 性能优化

- 代理插件采用轻量级设计，对性能影响最小
- 插件文件动态生成，避免冗余
- 自动资源清理，防止临时文件累积
- 支持插件缓存，减少重复创建开销

## 安全考虑

- 代理密码通过环境变量传递，避免硬编码
- 配置文件权限限制，确保安全性
- 扩展权限最小化，只请求必要权限
- 支持代理认证失败时的降级处理

## 版本历史

- **v1.0** - 初始版本，支持基本代理功能
- **v1.1** - 修复认证弹框问题
- **v1.2** - 优化User-Agent设置，支持桌面版访问
- **v1.3** - 完善文档和故障排除指南

---

*最后更新时间：2025年8月*
