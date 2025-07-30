# SpotLight 三大架构层整合文档

## 📋 概述

SpotLight 平台采用三层架构设计，将业务代码、容器化部署和 Selenium 修改有机整合，形成完整的自动化测试解决方案。

---

## 🏗️ 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    SpotLight 三层架构                           │
├─────────────────────────────────────────────────────────────────┤
│  📱 业务代码层 (mini/)                                         │
│  ├── hybrid_driver/     # 核心服务实现                        │
│  ├── scripts/           # 管理脚本                            │
│  ├── tests/             # 测试用例                            │
│  └── docs/              # 详细文档                            │
├─────────────────────────────────────────────────────────────────┤
│  🐳 容器化架构层 (mini/docker/)                               │
│  ├── 自定义 Selenium 镜像                                      │
│  ├── ADB 集成功能                                           │
│  ├── 代理服务 (ADB Proxy)                                     │
│  └── 集群部署方案                                           │
├─────────────────────────────────────────────────────────────────┤
│  🔧 Selenium 修改层 (@/selenium/)                            │
│  ├── 协议扩展                                              │
│  ├── 参数增强                                              │
│  └── 功能定制                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📱 第一层：业务代码层 (mini/)

### 核心功能

#### 1. 混合驱动服务
- **双执行器支持**: Selenium 和 Appium 统一管理
- **工厂模式**: 动态选择执行器类型
- **类型安全**: 统一的 WebExecutor 接口
- **向后兼容**: 保持现有 API 兼容性

#### 2. 模块化 API 设计
```
hybrid_driver/api/
├── routers/
│   ├── device.py      # 设备管理
│   ├── element.py     # 元素操作
│   ├── page.py        # 页面管理
│   ├── collect.py     # 数据收集
│   └── mock.py        # 模拟测试
├── models.py          # 数据模型
└── utils.py           # 工具函数
```

#### 3. 设备管理
- **设备池**: 多设备并发管理
- **连接管理**: 设备连接和断开
- **状态监控**: 实时设备状态监控

### 技术特点

- **异步架构**: 基于 FastAPI 的异步处理
- **模块化设计**: 按功能分离，便于维护
- **类型安全**: 完整的类型注解
- **测试覆盖**: 完整的测试套件

---

## 🐳 第二层：容器化架构层 (mini/docker/)

### 核心组件

#### 1. 自定义 Selenium 镜像
```dockerfile
# 基础镜像
FROM selenium/standalone-chrome:4.34.0-20250707

# 自定义功能
COPY scripts/custom_startup.sh /opt/bin/
RUN chmod +x /opt/bin/custom_startup.sh

# 启动命令
CMD ["/opt/bin/custom_startup.sh"]
```

#### 2. ADB 集成功能
- **ADB 预装**: 镜像中预装 ADB 工具
- **自动初始化**: 容器启动时自动启动 ADB 服务器
- **设备连接**: 支持 USB 和网络设备连接
- **权限支持**: 支持 USB 设备访问（特权模式）

#### 3. ADB Proxy 代理服务
```python
# 代理服务架构
class ProxyConnection:
    async def pipe(self, reader, writer, direction, hook, which):
        """异步数据管道处理"""
        while True:
            data = await reader.read(1024)
            if not data:
                break
            # 应用 hook 处理
            modified_data = await hook(data)
            writer.write(modified_data)
            await writer.drain()
```

### 容器编排

#### 1. 基础服务
```yaml
# docker-compose.custom-selenium.yml
services:
  custom-selenium-chrome:
    build:
      context: .
      dockerfile: Dockerfile.custom-selenium-chrome
    ports:
      - "4444:4444"
    environment:
      - SE_NODE_MAX_SESSIONS=4
```

#### 2. ADB 集成服务
```yaml
# docker-compose.custom-selenium-adb.yml
services:
  custom-selenium-chrome-adb:
    build:
      context: .
      dockerfile: Dockerfile.custom-selenium-chrome
    privileged: true  # 支持 USB 设备访问
    volumes:
      - /dev/bus/usb:/dev/bus/usb
    environment:
      - ADB_ENABLED=true
```

#### 3. 代理服务
```yaml
# docker-compose.adb-proxy.yml
services:
  adb-proxy:
    build:
      context: ./scripts/proxy
      dockerfile: Dockerfile
    ports:
      - "5037:5037"
    volumes:
      - /tmp:/tmp
```

### 部署方案

#### 1. 单机部署
```bash
# 启动基础服务
docker compose -f docker-compose.custom-selenium.yml up -d

# 启动 ADB 服务
docker compose -f docker-compose.custom-selenium-adb.yml up -d

# 启动代理服务
docker compose -f docker-compose.adb-proxy.yml up -d
```

#### 2. 集群部署
```bash
# 动态扩容
docker compose -f docker-compose.custom-selenium.yml up -d --scale custom-selenium-chrome=3

# 负载均衡
docker compose -f docker-compose.adb-proxy.yml up -d --scale adb-proxy=2
```

---

## 🔧 第三层：Selenium 修改层 (@/selenium/)

### 协议扩展

#### 1. WebDriver 协议增强
```python
# 标准 capabilities
capabilities = {
    "platformName": "Android",
    "appium:automationName": "UiAutomator2",
    "appium:deviceName": "Pixel_5",
    "browserName": "chrome"
}

# SpotLight 扩展 capabilities
capabilities.update({
    "se:userId": "u10_123",           # 用户隔离
    "se:devicePool": "pool1",         # 设备池
    "se:executorType": "selenium",     # 执行器类型
    "se:proxyEnabled": True,           # 代理启用
    "se:customParams": {               # 自定义参数
        "adbPort": 5037,
        "proxyPort": 5038
    }
})
```

#### 2. 命令拦截和修改
```python
# 原始 ADB 命令
adb shell ps && ps -A

# 经过代理修改后的命令
adb shell ps && ps -A | grep 'u10_123'
```

#### 3. 参数传递机制
```python
# 用户 ID 传递
def get_user_id_from_file():
    """从文件读取 userId"""
    try:
        if os.path.exists(USER_ID_FILE_PATH):
            with open(USER_ID_FILE_PATH, 'r', encoding='utf-8') as f:
                user_id = f.read().strip()
                if user_id:
                    return user_id
    except Exception as e:
        logger.error(f"读取 userId 文件失败: {e}")
    return "u10_"
```

### 构建和集成

#### 1. Selenium 构建
```bash
# 使用 Bazel 构建
cd selenium
bazel build //py:selenium

# 或使用传统方式
python setup.py build
```

#### 2. 集成到 SpotLight
```bash
# 安装自定义 Selenium
pip install -e selenium/py

# 验证安装
python -c "import selenium; print(selenium.__version__)"
```

---

## 🔄 三层架构整合

### 数据流

```
用户请求 → 业务代码层 → 容器化层 → Selenium 修改层 → Android 设备
    ↑                                                      ↓
    ←─────────────── 响应数据流 ────────────────────────────←
```

### 配置传递

#### 1. 用户配置
```python
# 业务代码层配置
config = {
    "executor_type": "selenium",
    "device_pool": "pool1",
    "user_id": "u10_123"
}

# 容器化层配置
docker_config = {
    "ADB_ENABLED": True,
    "PROXY_ENABLED": True,
    "USER_ID": "u10_123"
}

# Selenium 层配置
selenium_config = {
    "se:userId": "u10_123",
    "se:proxyEnabled": True
}
```

#### 2. 环境变量传递
```bash
# 启动容器时传递配置
docker run -e USER_ID=u10_123 -e PROXY_ENABLED=true custom-selenium-chrome-adb
```

### 错误处理

#### 1. 分层错误处理
```python
# 业务代码层
try:
    result = await device_operation()
except DeviceConnectionError:
    # 设备连接错误处理
    await retry_connection()
except SeleniumError:
    # Selenium 错误处理
    await switch_executor()

# 容器化层
try:
    container_operation()
except ContainerError:
    # 容器错误处理
    await restart_container()

# Selenium 层
try:
    selenium_operation()
except WebDriverException:
    # WebDriver 错误处理
    await handle_webdriver_error()
```

#### 2. 日志统一
```python
# 统一日志格式
logger.info(f"[{layer}] {operation}: {status}")
# 示例: [业务层] 设备连接: 成功
# 示例: [容器层] ADB 启动: 成功
# 示例: [Selenium层] 元素查找: 成功
```

---

## 🧪 测试验证

### 集成测试

#### 1. 端到端测试
```python
async def test_end_to_end_flow():
    """测试完整的数据流"""
    # 1. 业务代码层测试
    device = await connect_device("test_device")
    
    # 2. 容器化层测试
    container = await start_container(device)
    
    # 3. Selenium 层测试
    driver = await create_webdriver(container)
    
    # 4. 执行操作
    element = await find_element(driver, "test_selector")
    await click_element(element)
    
    # 5. 验证结果
    assert await verify_operation_success()
```

#### 2. 性能测试
```python
async def test_performance():
    """测试三层架构性能"""
    # 并发测试
    tasks = []
    for i in range(10):
        task = test_single_flow(f"device_{i}")
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # 性能指标
    avg_response_time = sum(r['response_time'] for r in results) / len(results)
    assert avg_response_time < 5.0  # 平均响应时间小于5秒
```

### 监控指标

#### 1. 业务层指标
- 设备连接成功率
- 操作执行时间
- 错误率统计

#### 2. 容器层指标
- 容器启动时间
- 资源使用率
- 网络连接状态

#### 3. Selenium 层指标
- WebDriver 创建时间
- 元素查找时间
- 页面加载时间

---

## 🔒 安全考虑

### 三层安全机制

#### 1. 业务代码层安全
- 用户身份验证
- 操作权限控制
- 数据加密传输

#### 2. 容器化层安全
- 容器隔离
- 资源限制
- 网络安全

#### 3. Selenium 层安全
- 协议安全
- 参数验证
- 错误处理

### 安全最佳实践

#### 1. 配置安全
```python
# 敏感配置加密
import os
from cryptography.fernet import Fernet

def encrypt_config(config):
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted_config = f.encrypt(config.encode())
    return encrypted_config
```

#### 2. 网络安全
```python
# 网络访问控制
def validate_network_access(ip, port):
    allowed_ips = ["192.168.1.0/24", "10.0.0.0/8"]
    return is_ip_allowed(ip, allowed_ips)
```

---

## 📊 性能优化

### 三层性能优化

#### 1. 业务代码层优化
- 异步处理
- 连接池管理
- 缓存机制

#### 2. 容器化层优化
- 镜像优化
- 资源限制
- 网络优化

#### 3. Selenium 层优化
- 驱动优化
- 会话管理
- 内存优化

### 性能监控

#### 1. 监控指标
```python
# 性能指标收集
metrics = {
    "business_layer": {
        "response_time": [],
        "error_rate": 0.0,
        "throughput": 0.0
    },
    "container_layer": {
        "startup_time": [],
        "resource_usage": {},
        "network_latency": []
    },
    "selenium_layer": {
        "webdriver_creation_time": [],
        "element_find_time": [],
        "page_load_time": []
    }
}
```

#### 2. 告警机制
```python
# 性能告警
def check_performance_alerts(metrics):
    if metrics['business_layer']['response_time'] > 5.0:
        send_alert("业务层响应时间过长")
    
    if metrics['container_layer']['resource_usage']['cpu'] > 80:
        send_alert("容器CPU使用率过高")
```

---

## 🔄 部署流程

### 完整部署流程

#### 1. 环境准备
```bash
# 1. 克隆项目
git clone <repository-url>
cd mini

# 2. 安装依赖
pip install -r requirements/requirements.txt

# 3. 构建容器镜像
cd docker
./build-adb-image.sh build
```

#### 2. 服务启动
```bash
# 1. 启动业务代码层
./start.sh start

# 2. 启动容器化层
docker compose -f docker-compose.custom-selenium-adb.yml up -d

# 3. 启动代理服务
docker compose -f docker-compose.adb-proxy.yml up -d
```

#### 3. 验证部署
```bash
# 1. 检查业务代码层
./start.sh status

# 2. 检查容器化层
docker compose -f docker-compose.custom-selenium-adb.yml ps

# 3. 检查代理服务
docker compose -f docker-compose.adb-proxy.yml ps

# 4. 运行测试
./start.sh test
```

### 自动化部署

#### 1. CI/CD 流程
```yaml
# .github/workflows/deploy.yml
name: Deploy SpotLight
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements/requirements.txt
      
      - name: Build containers
        run: |
          cd docker
          ./build-adb-image.sh build
      
      - name: Deploy services
        run: |
          ./start.sh start
          docker compose -f docker/docker-compose.custom-selenium-adb.yml up -d
          docker compose -f docker/docker-compose.adb-proxy.yml up -d
      
      - name: Run tests
        run: |
          ./start.sh test
```

---

## 📝 总结

### 架构优势

1. **模块化设计**: 三层架构清晰分离，便于维护和扩展
2. **技术栈统一**: 使用现代化的技术栈（FastAPI、Docker、Selenium）
3. **性能优化**: 异步处理、容器化部署、协议优化
4. **安全可靠**: 多层安全机制，确保系统安全
5. **易于部署**: 完整的部署流程和自动化工具

### 技术亮点

1. **混合驱动**: 统一支持 Selenium 和 Appium
2. **容器化部署**: 完整的 Docker 部署方案
3. **代理服务**: 智能的 ADB 代理和命令修改
4. **异步架构**: 基于 FastAPI 的高性能异步处理
5. **模块化 API**: 清晰的 API 设计和路由组织

### 未来规划

1. **Kubernetes 部署**: 支持 K8s 集群部署
2. **微服务架构**: 进一步拆分服务模块
3. **AI 集成**: 集成 AI 功能，提升自动化能力
4. **云原生**: 完全云原生架构设计
5. **多语言支持**: 支持更多编程语言

---

*最后更新时间: 2024-12-19* 