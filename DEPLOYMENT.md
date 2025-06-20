# SpotLight Script服务部署指南

## 概述

本文档提供了SpotLight Script服务的完整部署指南，包括环境准备、安装配置、运行维护和故障排除等内容。

## 环境要求

### 1. 系统要求

#### 操作系统
- **推荐**: Ubuntu 20.04 LTS / CentOS 8+
- **最低**: Ubuntu 18.04 LTS / CentOS 7+
- **架构**: x86_64 / ARM64

#### 硬件要求
- **CPU**: 4核心以上
- **内存**: 8GB以上
- **存储**: 50GB可用空间
- **网络**: 稳定的网络连接

### 2. 软件依赖

#### Python环境
```bash
# Python版本要求
Python 3.8+
pip 20.0+

# 检查Python版本
python3 --version
pip3 --version
```

#### 系统依赖
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-pip \
    python3-venv

# CentOS/RHEL
sudo yum update -y
sudo yum install -y \
    curl \
    wget \
    git \
    gcc \
    gcc-c++ \
    openssl-devel \
    libffi-devel \
    python3-devel \
    python3-pip
```

#### Chrome/Chromium浏览器
```bash
# Ubuntu/Debian
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# CentOS/RHEL
sudo yum install -y chromium
```

#### ADB工具
```bash
# 安装ADB
sudo apt install -y android-tools-adb  # Ubuntu/Debian
sudo yum install -y android-tools      # CentOS/RHEL

# 验证安装
adb version
```

## 安装部署

### 1. 获取代码

```bash
# 克隆项目
git clone <repository_url>
cd spot_light

# 或下载源码包
wget <download_url>
tar -xzf spotlight.tar.gz
cd spot_light
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

### 3. 安装Python依赖

```bash
# 升级pip
pip install --upgrade pip

# 安装依赖
cd script
pip install -r requirements.txt

# 验证安装
python -c "import selenium; print('Selenium installed successfully')"
```

### 4. 配置环境变量

```bash
# 创建配置文件
cat > .env << EOF
# 服务配置
HOST=0.0.0.0
PORT=8000
WORKERS=4

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/spotlight.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=7

# WebDriver配置
CHROME_VERSION=134.0.6998.136
ANDROID_PACKAGE=com.tencent.mm
ANDROID_PROCESS=com.tencent.mm:appbrand0

# 设备池配置
MAX_DEVICES=10
CLEANUP_INTERVAL=600
DEVICE_TIMEOUT=1800

# 安全配置
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
EOF

# 加载环境变量
export $(cat .env | xargs)
```

### 5. 创建必要目录

```bash
# 创建日志目录
mkdir -p logs
mkdir -p uploads

# 设置权限
chmod 755 logs uploads
```

### 6. 配置日志

```bash
# 创建日志配置文件
cat > log_config.py << EOF
import logging
import logging.handlers
import os

def setup_logging():
    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/spotlight.log',
        maxBytes=100*1024*1024,  # 100MB
        backupCount=7
    )
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

if __name__ == "__main__":
    setup_logging()
EOF
```

## 运行服务

### 1. 开发环境运行

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务
cd script
python main.py
```

### 2. 生产环境运行

#### 使用Uvicorn
```bash
# 直接运行
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4

# 后台运行
nohup uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4 > logs/uvicorn.log 2>&1 &
```

#### 使用Gunicorn
```bash
# 安装Gunicorn
pip install gunicorn

# 运行服务
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. 使用Systemd服务

```bash
# 创建服务文件
sudo tee /etc/systemd/system/spotlight.service << EOF
[Unit]
Description=SpotLight Script Service
After=network.target

[Service]
Type=exec
User=spotlight
Group=spotlight
WorkingDirectory=/opt/spotlight/script
Environment=PATH=/opt/spotlight/venv/bin
ExecStart=/opt/spotlight/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 创建用户
sudo useradd -r -s /bin/false spotlight

# 设置权限
sudo chown -R spotlight:spotlight /opt/spotlight

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable spotlight
sudo systemctl start spotlight

# 检查状态
sudo systemctl status spotlight
```

## Docker部署

### 1. 创建Dockerfile

```dockerfile
# 使用官方Python镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 安装ADB
RUN apt-get update && apt-get install -y android-tools-adb \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY script/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY script/ .

# 创建日志目录
RUN mkdir -p logs uploads

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2. 创建docker-compose.yml

```yaml
version: '3.8'

services:
  spotlight:
    build: script
    container_name: spotlight-service
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    environment:
      - LOG_LEVEL=INFO
      - HOST=0.0.0.0
      - PORT=8000
    restart: unless-stopped
    networks:
      - spotlight-network

networks:
  spotlight-network:
    driver: bridge
```

### 3. 构建和运行

```bash
# 构建镜像
docker build -t spotlight:latest .

# 运行容器
docker run -d \
  --name spotlight \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/uploads:/app/uploads \
  spotlight:latest

# 使用docker-compose
docker-compose up -d
```

## 配置管理

### 1. 配置文件结构

```
script/
├── config/
│   ├── __init__.py
│   ├── settings.py          # 主配置文件
│   ├── development.py       # 开发环境配置
│   ├── production.py        # 生产环境配置
│   └── testing.py           # 测试环境配置
├── .env                     # 环境变量文件
└── config.yaml             # YAML配置文件
```

### 2. 配置示例

#### settings.py
```python
import os
from typing import List

class Settings:
    # 基础配置
    PROJECT_NAME: str = "SpotLight Script Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/spotlight.log")
    LOG_MAX_SIZE: int = int(os.getenv("LOG_MAX_SIZE", "100MB").replace("MB", "")) * 1024 * 1024
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "7"))
    
    # WebDriver配置
    CHROME_VERSION: str = os.getenv("CHROME_VERSION", "134.0.6998.136")
    ANDROID_PACKAGE: str = os.getenv("ANDROID_PACKAGE", "com.tencent.mm")
    ANDROID_PROCESS: str = os.getenv("ANDROID_PROCESS", "com.tencent.mm:appbrand0")
    
    # 设备池配置
    MAX_DEVICES: int = int(os.getenv("MAX_DEVICES", "10"))
    CLEANUP_INTERVAL: int = int(os.getenv("CLEANUP_INTERVAL", "600"))
    DEVICE_TIMEOUT: int = int(os.getenv("DEVICE_TIMEOUT", "1800"))
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALLOWED_HOSTS: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

settings = Settings()
```

### 3. 环境特定配置

#### development.py
```python
from .settings import Settings

class DevelopmentSettings(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    WORKERS: int = 1
```

#### production.py
```python
from .settings import Settings

class ProductionSettings(Settings):
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    WORKERS: int = 4
    SECRET_KEY: str = "production-secret-key"
```

## 监控和维护

### 1. 健康检查

```bash
# 检查服务状态
curl -f http://localhost:8000/health

# 检查设备连接状态
curl -X POST http://localhost:8000/status \
  -H "Content-Type: application/json"
```

### 2. 日志监控

```bash
# 查看实时日志
tail -f logs/spotlight.log

# 查看错误日志
grep "ERROR" logs/spotlight.log

# 查看特定设备的日志
grep "serial_id=DEVICE_ID" logs/spotlight.log
```

### 3. 性能监控

```bash
# 检查进程状态
ps aux | grep uvicorn

# 检查内存使用
free -h

# 检查磁盘使用
df -h

# 检查网络连接
netstat -tulpn | grep 8000
```

### 4. 备份和恢复

```bash
# 备份配置和日志
tar -czf spotlight_backup_$(date +%Y%m%d).tar.gz \
    script/config/ \
    script/logs/ \
    script/uploads/ \
    .env

# 恢复备份
tar -xzf spotlight_backup_20240101.tar.gz
```

## 故障排除

### 1. 常见问题

#### 服务启动失败
```bash
# 检查端口占用
sudo netstat -tulpn | grep 8000

# 检查权限
ls -la logs/ uploads/

# 检查依赖
pip list | grep -E "(fastapi|uvicorn|selenium)"
```

#### WebDriver连接失败
```bash
# 检查Chrome安装
google-chrome --version

# 检查ChromeDriver
which chromedriver

# 检查ADB连接
adb devices
```

#### 设备连接失败
```bash
# 检查网络连通性
ping <android_device_ip>

# 检查ADB连接
adb connect <device_ip:port>

# 检查设备状态
adb shell getprop ro.build.version.release
```

### 2. 调试技巧

#### 启用调试模式
```bash
# 设置调试环境变量
export LOG_LEVEL=DEBUG
export DEBUG=true

# 启动调试服务
python main.py
```

#### 查看详细日志
```bash
# 查看所有日志级别
tail -f logs/spotlight.log | grep -E "(DEBUG|INFO|WARNING|ERROR)"

# 查看特定操作日志
tail -f logs/spotlight.log | grep "ACTION_"
```

### 3. 性能优化

#### 连接池优化
```python
# 调整设备池配置
MAX_DEVICES = 20
CLEANUP_INTERVAL = 300
DEVICE_TIMEOUT = 900
```

#### 内存优化
```python
# 启用垃圾回收
import gc
gc.enable()

# 定期清理
def cleanup_memory():
    gc.collect()
```

## 安全配置

### 1. 网络安全

#### 防火墙配置
```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

#### SSL/TLS配置
```bash
# 生成SSL证书
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# 使用HTTPS
uvicorn server:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

### 2. 访问控制

#### API认证
```python
# 添加API密钥认证
from fastapi import HTTPException, Depends, Header

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.post("/connect")
async def connect(req: ConnectRequest, api_key: str = Depends(verify_api_key)):
    # 连接逻辑
    pass
```

#### 请求限流
```python
# 添加限流中间件
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/connect")
@limiter.limit("10/minute")
async def connect(req: ConnectRequest):
    # 连接逻辑
    pass
```

## 更新和升级

### 1. 版本升级

```bash
# 备份当前版本
cp -r script script_backup_$(date +%Y%m%d)

# 更新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
sudo systemctl restart spotlight
```

### 2. 回滚操作

```bash
# 恢复备份
rm -rf script
cp -r script_backup_20240101 script

# 重启服务
sudo systemctl restart spotlight
```

## 总结

本文档提供了SpotLight Script服务的完整部署指南。通过遵循这些步骤，您可以成功部署和维护一个高可用、高性能的自动化操作服务。

关键要点：
1. **环境准备**: 确保所有依赖正确安装
2. **配置管理**: 使用环境变量和配置文件
3. **监控维护**: 定期检查服务状态和性能
4. **安全防护**: 实施适当的安全措施
5. **故障排除**: 掌握常见问题的解决方法

如有问题，请参考故障排除部分或联系技术支持。 