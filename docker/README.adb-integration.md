# 带 ADB 功能的自定义 Selenium Chrome 镜像使用指南

## 概述

这个自定义镜像基于 `selenium/standalone-chrome:4.34.0-20250707`，集成了 ADB (Android Debug Bridge) 功能，可以在容器启动时执行自定义脚本，并支持 Android 设备调试。

## 新增功能

### ✅ ADB 集成特性
- **ADB 安装**: 镜像中预装了 ADB 工具
- **自动初始化**: 容器启动时自动启动 ADB 服务器
- **设备连接**: 支持连接 Android 设备（USB 或网络）
- **日志记录**: 完整的 ADB 操作日志记录
- **权限支持**: 支持 USB 设备访问（需要特权模式）

## 文件结构

```
mini/docker/
├── Dockerfile.custom-selenium-chrome    # 自定义镜像 Dockerfile（已更新）
├── docker-compose.custom-selenium-adb.yml  # 带 ADB 的 Docker Compose 配置
├── build-adb-image.sh                   # ADB 镜像构建脚本
├── scripts/
│   ├── custom_startup.sh               # 自定义启动脚本（已更新）
│   └── adb_init.sh                    # ADB 初始化脚本
└── README.adb-integration.md           # 本说明文档
```

## 快速开始

### 1. 构建带 ADB 功能的镜像

```bash
cd mini/docker
./build-adb-image.sh build
```

### 2. 构建并测试镜像

```bash
./build-adb-image.sh test
```

### 3. 启动服务

```bash
# 启动生产模式实例
docker compose -f docker-compose.custom-selenium-adb.yml up -d custom-selenium-chrome-adb

# 启动调试模式实例
docker compose -f docker-compose.custom-selenium-adb.yml up -d custom-selenium-chrome-adb-debug
```

### 4. 进入容器执行 ADB 命令

```bash
./build-adb-image.sh adb
```

## ADB 功能使用

### 1. 基本 ADB 命令

进入容器后，可以执行以下 ADB 命令：

```bash
# 查看连接的设备
adb devices

# 查看设备信息
adb shell getprop ro.product.model

# 安装 APK
adb install /path/to/app.apk

# 卸载应用
adb uninstall com.example.app

# 截图
adb shell screencap /sdcard/screenshot.png
adb pull /sdcard/screenshot.png

# 录屏
adb shell screenrecord /sdcard/video.mp4
adb pull /sdcard/video.mp4
```

### 2. 连接网络设备

```bash
# 连接到网络设备
adb connect 192.168.1.100:5555

# 断开连接
adb disconnect 192.168.1.100:5555
```

### 3. 文件传输

```bash
# 推送文件到设备
adb push local_file.txt /sdcard/

# 从设备拉取文件
adb pull /sdcard/remote_file.txt ./
```

## 环境变量配置

### ADB 相关环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ADB_DEVICE_IP` | 自动连接的设备 IP | `192.168.1.100:5555` |

### 在 docker-compose 中配置

```yaml
environment:
  - ADB_DEVICE_IP=192.168.1.100:5555
```

## 设备访问配置

### 1. USB 设备访问

要访问 USB 连接的 Android 设备，需要：

```yaml
# 在 docker-compose 中配置
devices:
  - /dev/bus/usb:/dev/bus/usb
privileged: true
```

### 2. 网络设备访问

对于网络连接的设备，只需要确保网络连通性：

```bash
# 在宿主机上连接设备
adb connect 192.168.1.100:5555
```

## 日志和监控

### 1. 查看 ADB 日志

```bash
# 查看容器日志
docker compose -f docker-compose.custom-selenium-adb.yml logs custom-selenium-chrome-adb

# 查看 ADB 初始化日志
docker exec <container_id> cat /opt/scripts/logs/adb/init.log
```

### 2. 实时监控 ADB 状态

```bash
# 进入容器监控 ADB
docker exec -it <container_id> bash
watch -n 1 'adb devices'
```

## 故障排除

### 1. ADB 服务器启动失败

```bash
# 重启 ADB 服务器
docker exec <container_id> adb kill-server
docker exec <container_id> adb start-server
```

### 2. 设备连接问题

```bash
# 检查设备连接状态
docker exec <container_id> adb devices

# 重新连接设备
docker exec <container_id> adb disconnect
docker exec <container_id> adb connect <device_ip>
```

### 3. 权限问题

如果遇到权限问题，确保容器以特权模式运行：

```yaml
privileged: true
```

## 高级用法

### 1. 自动化脚本

在自定义启动脚本中添加 ADB 自动化：

```bash
#!/bin/bash
# 在 custom_startup.sh 中添加

# 等待设备连接
echo "等待 Android 设备连接..."
while [ $(adb devices | grep -v "List of devices" | grep -v "^$" | wc -l) -eq 0 ]; do
    sleep 2
done

# 执行自动化操作
adb shell input tap 100 200  # 点击屏幕
adb shell input text "hello"  # 输入文本
```

### 2. 批量操作

```bash
# 批量安装 APK
for apk in /opt/apks/*.apk; do
    adb install "$apk"
done

# 批量截图
adb shell screencap /sdcard/screenshot_$(date +%s).png
```

### 3. 与 Selenium 集成

结合 Selenium 和 ADB 进行混合自动化：

```python
# Python 示例
import subprocess

def adb_command(cmd):
    result = subprocess.run(['adb'] + cmd.split(), capture_output=True, text=True)
    return result.stdout

# 使用 ADB 操作 Android 设备
adb_command('shell input tap 100 200')
adb_command('shell input text "test"')
```

## 性能优化

### 1. 内存配置

```yaml
services:
  custom-selenium-chrome-adb:
    shm_size: 2gb
    mem_limit: 4g
```

### 2. 并发配置

```yaml
services:
  custom-selenium-chrome-adb:
    environment:
      - SE_NODE_MAX_SESSIONS=8
```

## 安全考虑

1. **USB 设备访问**: 需要特权模式，注意安全风险
2. **网络连接**: 确保网络设备的安全性
3. **日志安全**: 避免在日志中记录敏感信息
4. **权限最小化**: 只授予必要的权限

## 集成到 SpotLight 项目

要将此带 ADB 功能的镜像集成到您的 SpotLight 项目中：

1. 复制相关文件到项目目录
2. 修改现有的 docker-compose 配置
3. 更新启动脚本以使用新的镜像
4. 配置 Android 设备连接
5. 测试集成功能

## 支持

如有问题，请查看：
- 容器日志: `docker logs <container_name>`
- ADB 初始化日志: `/opt/scripts/logs/adb/init.log`
- ADB 设备状态: `adb devices`
- 项目文档: `mini/README.md` 