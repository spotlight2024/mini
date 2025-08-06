# Chrome代理扩展完全动态生成方案

## 🎯 方案概述

本方案采用完全动态生成的方式创建Chrome代理扩展，相比之前的混合模式（静态文件+动态配置），具有更好的维护性和灵活性。

## 🔄 方案对比

### 旧方案（混合模式）
```
静态文件 + 动态配置
├── chrome_extensions/proxy_auth/     # 静态文件
│   ├── manifest.json                # 静态文件
│   ├── background.js                # 静态文件
│   └── config.js                    # 模板文件
└── setup_proxy_config.sh            # 动态修改静态文件
```

**问题：**
- 需要维护静态文件和动态生成逻辑
- 文件修改可能导致权限问题
- 调试时难以确定配置来源
- 版本控制复杂

### 新方案（完全动态生成）
```
完全动态生成
├── setup_proxy_config.sh            # 动态生成所有文件
│   ├── generate_manifest()          # 生成manifest.json
│   ├── generate_background_js()     # 生成background.js
│   ├── generate_proxy_config()      # 生成proxy_config.json
│   └── set_permissions()            # 设置文件权限
└── 无静态文件依赖
```

**优势：**
- ✅ 单一职责：只需维护生成脚本
- ✅ 清晰逻辑：配置逻辑集中在一个地方
- ✅ 易于调试：配置来源明确
- ✅ 版本控制简单：只需管理脚本文件
- ✅ 灵活配置：支持命令行参数和环境变量

## 🚀 使用方法

### 1. 命令行参数方式

```bash
# 基本用法
./scripts/setup_proxy_config.sh \
    --host 61.132.231.167 \
    --port 57001 \
    --username vgmpgv \
    --password 1bk79g9y \
    --enabled true

# 指定扩展目录
./scripts/setup_proxy_config.sh \
    --host 192.168.1.100 \
    --port 8080 \
    --dir /custom/extension/path

# 禁用代理
./scripts/setup_proxy_config.sh \
    --host 192.168.1.100 \
    --port 8080 \
    --enabled false
```

### 2. 环境变量方式

```bash
# 设置环境变量
export PROXY_HOST=61.132.231.167
export PROXY_PORT=57001
export PROXY_USERNAME=vgmpgv
export PROXY_PASSWORD=1bk79g9y
export PROXY_ENABLED=true

# 运行脚本（自动读取环境变量）
./scripts/setup_proxy_config.sh
```

### 3. Docker容器中使用

```bash
# 在容器中测试
docker exec chrome-driver /opt/custom-scripts/setup_proxy_config.sh \
    --host 61.132.231.167 \
    --port 57001 \
    --username vgmpgv \
    --password 1bk79g9y

# 使用环境变量
docker run -e PROXY_HOST=61.132.231.167 \
    -e PROXY_PORT=57001 \
    -e PROXY_USERNAME=vgmpgv \
    -e PROXY_PASSWORD=1bk79g9y \
    -e PROXY_ENABLED=true \
    custom-selenium-chrome:adb_proxy
```

## 📋 参数说明

| 参数 | 短参数 | 必需 | 说明 | 示例 |
|------|--------|------|------|------|
| `--host` | `-h` | 是 | 代理服务器地址 | `61.132.231.167` |
| `--port` | `-p` | 是 | 代理服务器端口 | `57001` |
| `--username` | `-u` | 否 | 代理用户名 | `vgmpgv` |
| `--password` | `-w` | 否 | 代理密码 | `1bk79g9y` |
| `--enabled` | `-e` | 否 | 是否启用代理 | `true`/`false` |
| `--dir` | `-d` | 否 | 扩展目录 | `/opt/chrome_extensions/proxy_auth` |
| `--help` | | | 显示帮助信息 | |

## 🔧 技术实现

### 1. 脚本结构

```bash
#!/bin/bash
# 完全动态生成Chrome代理扩展

# 函数：显示使用说明
show_usage() { ... }

# 函数：生成manifest.json
generate_manifest() { ... }

# 函数：生成background.js
generate_background_js() { ... }

# 函数：生成proxy_config.json
generate_proxy_config() { ... }

# 函数：设置文件权限
set_permissions() { ... }

# 主函数：生成完整的Chrome扩展
generate_extension() { ... }

# 解析命令行参数
parse_arguments() { ... }

# 主程序
main() { ... }
```

### 2. 生成的文件

#### manifest.json
```json
{
  "manifest_version": 3,
  "name": "Auto Proxy Auth",
  "version": "1.0",
  "description": "Automatically authenticate HTTP proxy without popup dialogs",
  "permissions": [
    "proxy",
    "webRequest",
    "webRequestAuthProvider"
  ],
  "host_permissions": [
    "<all_urls>"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "web_accessible_resources": [
    {
      "resources": ["proxy_config.json"],
      "matches": ["<all_urls>"]
    }
  ]
}
```

#### background.js
```javascript
// 动态生成的代理配置
let proxyConfig = {
  host: '61.132.231.167',
  port: '57001',
  username: 'vgmpgv',
  password: '1bk79g9y',
  enabled: true
};

// 代理设置和认证处理逻辑
function updateProxySettings() { ... }
chrome.webRequest.onAuthRequired.addListener(...)
```

#### proxy_config.json
```json
{
  "host": "61.132.231.167",
  "port": "57001",
  "username": "vgmpgv",
  "password": "1bk79g9y",
  "enabled": true
}
```

## 🧪 测试验证

### 1. 构建和测试流程

```bash
# 完整构建和测试流程
cd mini/docker
./build_and_test.sh

# 仅构建镜像
./build_and_test.sh --build-only

# 仅运行测试
./build_and_test.sh --test-only

# 测试Docker Compose集成
./build_and_test.sh --compose-test
```

### 2. 容器内测试

```bash
# 在容器中运行测试
docker exec chrome-driver /opt/custom-scripts/test_in_container.sh
```

### 3. 验证生成的文件

```bash
# 检查扩展目录
ls -la /opt/chrome_extensions/proxy_auth/

# 验证manifest.json格式
python3 -m json.tool /opt/chrome_extensions/proxy_auth/manifest.json

# 验证proxy_config.json格式
python3 -m json.tool /opt/chrome_extensions/proxy_auth/proxy_config.json

# 检查配置参数注入
grep "host: '61.132.231.167'" /opt/chrome_extensions/proxy_auth/background.js
```

## 🔍 调试方法

### 1. 查看生成的文件

```bash
# 查看所有生成的文件
ls -la /opt/chrome_extensions/proxy_auth/

# 查看manifest.json
cat /opt/chrome_extensions/proxy_auth/manifest.json

# 查看background.js（前20行）
head -20 /opt/chrome_extensions/proxy_auth/background.js

# 查看proxy_config.json
cat /opt/chrome_extensions/proxy_auth/proxy_config.json
```

### 2. 检查配置参数

```bash
# 检查主机参数
grep "host:" /opt/chrome_extensions/proxy_auth/background.js

# 检查端口参数
grep "port:" /opt/chrome_extensions/proxy_auth/background.js

# 检查用户名参数
grep "username:" /opt/chrome_extensions/proxy_auth/background.js
```

### 3. 验证Chrome包装脚本

```bash
# 检查包装脚本
cat /usr/local/bin/chrome-with-proxy

# 检查Chrome符号链接
ls -la /usr/bin/google-chrome
```

## 📊 性能优势

### 1. 构建时间
- **旧方案**：需要复制静态文件 + 修改配置
- **新方案**：直接生成所有文件，速度更快

### 2. 维护成本
- **旧方案**：需要维护静态文件和动态逻辑
- **新方案**：只需维护生成脚本

### 3. 调试效率
- **旧方案**：需要检查多个文件来源
- **新方案**：配置来源明确，调试简单

### 4. 版本控制
- **旧方案**：需要管理静态文件和脚本
- **新方案**：只需管理脚本文件

## 🚀 部署流程

### 1. 开发环境

```bash
# 1. 构建镜像
cd mini/docker
./build_and_test.sh --build-only

# 2. 启动测试容器
docker run -d --name test-proxy \
    -e PROXY_HOST=192.168.1.100 \
    -e PROXY_PORT=8080 \
    custom-selenium-chrome:adb_proxy

# 3. 运行测试
docker exec test-proxy /opt/custom-scripts/test_in_container.sh
```

### 2. 生产环境

```bash
# 1. 构建生产镜像
docker build -f Dockerfile.custom-selenium-chrome \
    -t custom-selenium-chrome:production .

# 2. 使用Docker Compose部署
docker compose --env-file proxy.env up -d

# 3. 验证部署
docker compose exec chrome-driver \
    /opt/custom-scripts/setup_proxy_config.sh --help
```

## 📝 最佳实践

### 1. 配置管理
- 使用环境变量管理敏感信息
- 将配置模板纳入版本控制
- 定期更新代理配置

### 2. 测试策略
- 在开发环境充分测试
- 使用自动化测试验证功能
- 定期进行集成测试

### 3. 监控告警
- 监控代理连接状态
- 检查Chrome扩展加载情况
- 记录代理认证日志

---

*完全动态生成方案 - 提供更简洁、更灵活的Chrome代理扩展管理*
