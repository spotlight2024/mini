# Chrome代理扩展使用指南

## 🎯 概述

Chrome代理扩展采用完全动态生成的方式，支持通过命令行参数或环境变量配置代理。所有Chrome扩展文件（manifest.json、background.js、proxy_config.json）都通过脚本动态生成，无需维护静态文件。

## 🚀 快速开始

### 1. 构建镜像
```bash
cd mini/docker
./build.sh --build-only
```

### 2. 启动服务
```bash
# 使用代理配置启动
docker compose --env-file proxy.env up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f chrome-driver
```

### 3. 测试功能
```bash
# 运行测试
./build.sh

# 或在容器中测试
docker exec chrome-driver /opt/custom-scripts/test.sh
```

## ⚙️ 配置方式

### 环境变量配置
编辑 `proxy.env` 文件：
```bash
# 启用代理
PROXY_ENABLED=true

# 代理服务器配置
PROXY_HOST=61.132.231.167
PROXY_PORT=57001
PROXY_USERNAME=vgmpgv
PROXY_PASSWORD=1bk79g9y
```

### 命令行参数
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

## 🔧 脚本使用

### build.sh - 构建脚本
```bash
# 构建镜像并测试
./build.sh

# 仅构建镜像
./build.sh --build-only

# 仅运行测试
./build.sh --test-only

# 构建并启动服务
./build.sh --start
```

### test.sh - 测试脚本
```bash
# 在容器中运行测试
docker exec chrome-driver /opt/custom-scripts/test.sh
```

## 🐳 Docker集成

### 镜像构建
```bash
# 构建镜像
docker build -f Dockerfile.custom-selenium-chrome -t custom-selenium-chrome:adb_proxy .
```

### 容器运行
```bash
# 使用环境变量
docker run -d --name chrome-proxy \
    -e PROXY_HOST=61.132.231.167 \
    -e PROXY_PORT=57001 \
    -e PROXY_USERNAME=vgmpgv \
    -e PROXY_PASSWORD=1bk79g9y \
    -e PROXY_ENABLED=true \
    custom-selenium-chrome:adb_proxy
```

### Docker Compose
```bash
# 启动服务
docker compose --env-file proxy.env up -d

# 停止服务
docker compose down

# 查看日志
docker compose logs -f chrome-driver
```

## 🔍 验证功能

### 1. 检查代理配置
```bash
# 查看代理配置文件
docker exec chrome-driver cat /opt/chrome_extensions/proxy_auth/proxy_config.json

# 检查Chrome扩展
docker exec chrome-driver ls -la /opt/chrome_extensions/proxy_auth/
```

### 2. 测试代理连接
```bash
# 测试代理连接
docker exec chrome-driver curl -x http://username:password@proxy_host:proxy_port http://httpbin.org/ip
```

### 3. 验证Chrome包装脚本
```bash
# 检查包装脚本
docker exec chrome-driver cat /usr/local/bin/chrome-with-proxy

# 检查Chrome符号链接
docker exec chrome-driver ls -la /usr/bin/google-chrome
```

## 🛠️ 故障排除

### 常见问题

1. **代理未生效**
   ```bash
   # 检查环境变量
   docker compose config | grep PROXY
   
   # 检查代理配置
   docker exec chrome-driver cat /opt/chrome_extensions/proxy_auth/proxy_config.json
   ```

2. **Chrome启动失败**
   ```bash
   # 检查镜像构建
   docker images | grep custom-selenium-chrome
   
   # 查看容器日志
   docker compose logs chrome-driver
   ```

3. **认证弹框问题**
   ```bash
   # 检查扩展加载
   docker exec chrome-driver ps aux | grep chrome | grep load-extension
   
   # 重启Chrome容器
   docker compose restart chrome-driver
   ```

### 调试命令
```bash
# 进入容器调试
docker exec -it chrome-driver bash

# 查看环境变量
docker exec chrome-driver env | grep PROXY

# 检查文件权限
docker exec chrome-driver ls -la /opt/chrome_extensions/proxy_auth/
```

## 📊 技术特性

### ✅ 核心功能
- **完全动态生成**：所有Chrome扩展文件都通过脚本动态生成
- **灵活配置**：支持命令行参数和环境变量两种配置方式
- **自动认证**：Chrome扩展自动处理HTTP代理认证，无弹框提示
- **反检测增强**：内置反爬虫检测绕过机制
- **容器化集成**：完全集成在Docker镜像中

### 🏗️ 架构优势
- **单一职责**：只需维护生成脚本
- **清晰逻辑**：配置逻辑集中在一个地方
- **易于调试**：配置来源明确
- **版本控制简单**：只需管理脚本文件

## 📚 相关文档

- [PROXY_SETUP.md](../docs/guides/PROXY_SETUP.md) - 详细使用指南
- [PROXY_DYNAMIC_GENERATION.md](../docs/guides/PROXY_DYNAMIC_GENERATION.md) - 技术实现说明

---

*Chrome代理扩展使用指南 - 提供简洁、灵活的代理解决方案*
