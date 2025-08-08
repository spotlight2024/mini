# 🚀 极速开始指南

## 1️⃣ 一键部署

```bash
# 1. 构建镜像
./build.sh

# 2. 启动服务
./start.sh start

# 3. 验证代理
python3 verify.py
```

## 2️⃣ 配置代理IP

编辑 `docker-compose.yml`：
```yaml
environment:
  - PROXY_HOST=你的代理IP
  - PROXY_PORT=你的代理端口
  - PROXY_USERNAME=你的用户名
  - PROXY_PASSWORD=你的密码
```

## 3️⃣ 使用示例

```python
from selenium import webdriver

driver = webdriver.Remote(
    command_executor='http://localhost:4444/wd/hub',
    options=webdriver.ChromeOptions()
)

driver.get("https://www.taobao.com")
print(f"访问成功: {driver.title}")
driver.quit()
```

## 4️⃣ 多节点扩展

```bash
# 1. 编辑代理列表
vim proxies.txt

# 2. 生成配置
python3 setup.py

# 3. 重新部署
./build.sh && ./start.sh start
```

## 5️⃣ 常用命令

```bash
# 查看Grid状态
curl localhost:4444/status

# 查看容器状态
docker compose ps

# 查看日志
./start.sh logs

# 停止服务
./start.sh stop

# 测试IP
./start.sh test
```

---
**⚡ 特点**: 零配置、完全透明、反作弊友好
