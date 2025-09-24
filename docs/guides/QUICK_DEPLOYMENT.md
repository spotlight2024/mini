# SpotLight 快速部署指南

## 📋 概述

本指南将帮助您快速部署 SpotLight 平台的三大架构层，包括业务代码层、容器化架构层和 Selenium 修改层。

---

## 🚀 一键部署

### 环境要求

- **操作系统**: Linux (Ubuntu 18.04+)
- **Python**: 3.9+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 至少 4GB RAM
- **存储**: 至少 10GB 可用空间

### 快速开始

#### 1. 克隆项目
```bash
git clone <repository-url>
cd mini
```

#### 2. 一键部署脚本
```bash
# 运行一键部署脚本
./scripts/deploy-all.sh

# 或者分步执行
./start.sh install      # 安装依赖
./start.sh start        # 启动业务代码层
cd docker && ./deploy-containers.sh  # 部署容器化层
```

#### 3. 验证部署
```bash
# 检查所有服务状态
./start.sh status

# 运行测试
./start.sh test

# 查看日志
./start.sh logs
```

---

## 📱 业务代码层部署

### 1. 环境准备
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
poetry install --with dev
```

### 2. 配置设置
```bash
# 复制环境配置文件
cp env.example .env

# 编辑配置文件
nano .env
```

### 3. 启动服务
```bash
# 启动主服务
./start.sh start

# 或者直接启动
python hybrid_driver/main.py
```

### 4. 验证服务
```bash
# 检查服务状态
curl http://localhost:8000/health

# 使用 CLI 工具
./start.sh cli status
```

---

## 🐳 容器化架构层部署

### 1. 构建镜像
```bash
cd docker

# 构建基础镜像
docker compose -f docker-compose.custom-selenium.yml build

# 构建带 ADB 功能的镜像
./build-adb-image.sh build
```

### 2. 启动容器服务
```bash
# 启动基础 Selenium 服务
docker compose -f docker-compose.custom-selenium.yml up -d

# 启动带 ADB 的服务
docker compose -f docker-compose.custom-selenium-adb.yml up -d

# 启动 ADB 代理服务
docker compose -f docker-compose.adb-proxy.yml up -d
```

### 3. 验证容器服务
```bash
# 检查容器状态
docker compose -f docker-compose.custom-selenium.yml ps

# 查看容器日志
docker compose -f docker-compose.custom-selenium.yml logs -f

# 测试 ADB 功能
./build-adb-image.sh test
```

### 4. 配置代理服务
```bash
# 启动 ADB 代理
cd scripts/proxy
python3 adb_proxy.py &

# 测试代理功能
python3 test_simple_user_id_flow.py
```

---

## 🔧 Selenium 修改层部署

### 1. 构建 Selenium
```bash
cd ../selenium

# 使用 Bazel 构建
bazel build //py:selenium

# 或使用传统方式
python setup.py build
```

### 2. 安装自定义 Selenium
```bash
# 安装到当前环境
pip install -e py/

# 验证安装
python -c "import selenium; print(selenium.__version__)"
```

### 3. 集成到 SpotLight
```bash
# 回到 mini 目录
cd ../mini

# 验证集成
python -c "
from selenium import webdriver
from selenium.webdriver.common.by import By
print('Selenium 集成成功')
"
```

---

## 🔄 完整部署流程

### 自动化部署脚本

创建 `scripts/deploy-all.sh`:

```bash
#!/bin/bash

echo "🚀 开始部署 SpotLight 平台..."

# 1. 环境检查
echo "📋 检查环境..."
python3 --version || { echo "❌ Python 3.9+ 未安装"; exit 1; }
docker --version || { echo "❌ Docker 未安装"; exit 1; }
docker compose version || { echo "❌ Docker Compose 未安装"; exit 1; }

# 2. 安装依赖
echo "📦 安装依赖..."
./start.sh install

# 3. 启动业务代码层
echo "📱 启动业务代码层..."
./start.sh start

# 4. 构建容器镜像
echo "🐳 构建容器镜像..."
cd docker
./build-adb-image.sh build

# 5. 启动容器服务
echo "🔧 启动容器服务..."
docker compose -f docker-compose.custom-selenium-adb.yml up -d
docker compose -f docker-compose.adb-proxy.yml up -d

# 6. 启动代理服务
echo "🔄 启动代理服务..."
cd scripts/proxy
python3 adb_proxy.py &
cd ../..

# 7. 验证部署
echo "✅ 验证部署..."
./start.sh status
./start.sh test

echo "🎉 SpotLight 平台部署完成！"
echo "📊 服务状态:"
echo "  - 业务代码层: http://localhost:8000"
echo "  - Selenium 服务: http://localhost:4444"
echo "  - ADB 代理: localhost:5037"
```

### 使用自动化部署
```bash
# 给脚本执行权限
chmod +x scripts/deploy-all.sh

# 运行自动化部署
./scripts/deploy-all.sh
```

---

## 🧪 测试验证

### 1. 单元测试
```bash
# 运行所有测试
./start.sh test

# 运行特定测试
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/functional/ -v
```

### 2. 容器测试
```bash
# 测试容器功能
cd docker
./build-and-test.sh

# 测试 ADB 功能
./build-adb-image.sh test
```

### 3. 代理测试
```bash
# 测试 ADB 代理
cd scripts/proxy
python3 test_simple_user_id_flow.py
python3 test_robust_user_id_flow.py
```

### 4. 端到端测试
```bash
# 运行端到端测试
python examples/test_end_to_end.py
```

---

## 📊 监控和日志

### 1. 服务监控
```bash
# 查看所有服务状态
./start.sh status

# 查看容器状态
docker compose -f docker/docker-compose.custom-selenium-adb.yml ps

# 查看代理状态
ps aux | grep adb_proxy
```

### 2. 日志查看
```bash
# 查看业务代码日志
./start.sh logs -f

# 查看容器日志
docker compose -f docker/docker-compose.custom-selenium-adb.yml logs -f

# 查看代理日志
tail -f docker/scripts/proxy/proxy.log
```

### 3. 性能监控
```bash
# 查看系统资源
htop

# 查看 Docker 资源
docker stats

# 查看网络连接
netstat -tlnp | grep -E "(8000|4444|5037)"
```

---

## 🔧 故障排除

### 常见问题

#### 1. 端口冲突
```bash
# 检查端口占用
netstat -tlnp | grep -E "(8000|4444|5037)"

# 停止冲突服务
sudo systemctl stop apache2  # 如果 8000 端口被占用
sudo systemctl stop nginx     # 如果 4444 端口被占用
```

#### 2. 权限问题
```bash
# 修复 Docker 权限
sudo usermod -aG docker $USER
newgrp docker

# 修复文件权限
chmod +x scripts/*.sh
chmod +x start.sh
```

#### 3. 依赖问题
```bash
# 重新安装依赖
poetry install --with dev

# 清理缓存
./start.sh clean
```

#### 4. 容器问题
```bash
# 重启容器
docker compose -f docker/docker-compose.custom-selenium-adb.yml restart

# 重建容器
docker compose -f docker/docker-compose.custom-selenium-adb.yml up -d --build
```

### 调试模式

#### 1. 启用调试日志
```bash
# 设置环境变量
export LOG_LEVEL=DEBUG
export ADB_PROXY_LOG_LEVEL=DEBUG

# 重启服务
./start.sh restart
```

#### 2. 进入容器调试
```bash
# 进入 Selenium 容器
docker exec -it custom-selenium-chrome-adb bash

# 进入代理容器
docker exec -it adb-proxy bash
```

---

## 📈 性能优化

### 1. 系统优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65535" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 2. Docker 优化
```bash
# 优化 Docker 配置
sudo tee /etc/docker/daemon.json <<EOF
{
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5,
  "storage-driver": "overlay2"
}
EOF

sudo systemctl restart docker
```

### 3. 应用优化
```python
# 优化线程池大小
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 根据 CPU 核心数设置
executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2)
asyncio.get_event_loop().set_default_executor(executor)
```

---

## 🔒 安全配置

### 1. 网络安全
```bash
# 配置防火墙
sudo ufw allow 8000/tcp   # 业务代码层
sudo ufw allow 4444/tcp   # Selenium 服务
sudo ufw allow 5037/tcp   # ADB 代理
sudo ufw enable
```

### 2. 容器安全
```bash
# 使用非 root 用户运行容器
docker run --user 1000:1000 custom-selenium-chrome-adb

# 限制容器资源
docker run --memory=2g --cpus=2 custom-selenium-chrome-adb
```

### 3. 应用安全
```python
# 启用 HTTPS
import uvicorn
from hybrid_driver.server import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="certs/key.pem",
        ssl_certfile="certs/cert.pem"
    )
```

---

## 📝 维护指南

### 1. 日常维护
```bash
# 每日检查
./start.sh status
docker system prune -f
./start.sh logs -e  # 查看错误日志
```

### 2. 定期更新
```bash
# 更新代码
git pull origin main

# 更新依赖
poetry install --with dev

# 重建容器
cd docker
./build-adb-image.sh build
```

### 3. 备份和恢复
```bash
# 备份配置
tar -czf backup-$(date +%Y%m%d).tar.gz config/ logs/

# 恢复配置
tar -xzf backup-20241219.tar.gz
```

---

## 📞 技术支持

### 获取帮助
- **文档**: [详细文档](docs/README.md)
- **FAQ**: [常见问题](docs/guides/faq.md)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **联系**: [维护者信息](docs/guides/contact.md)

### 日志收集
```bash
# 收集诊断信息
./scripts/collect-diagnostics.sh

# 生成诊断报告
python scripts/generate-report.py
```

---

*最后更新时间: 2025-07-30* 