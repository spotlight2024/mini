# SpotLight 混合驱动自动化平台

## 一、项目简介

SpotLight 是面向 Android 虚拟机自动化的云端混合驱动平台，支持微信小程序/WebView/原生自动化，具备多设备并发、智能指令、弹窗处理、数据采集等能力。

---

## 二、架构总览

```
用户指令 → Android虚拟机APP → 云服务器Script服务 → 混合WebDriver → 微信小程序/WebView
```

### 核心架构特点
- **混合驱动支持**: 统一支持 Selenium 和 Appium 两种 WebDriver 实现
- **工厂模式**: 通过 `ExecutorFactory` 动态选择执行器类型
- **类型安全**: 统一的 `WebExecutor` 接口，确保类型安全
- **向后兼容**: 保持现有 API 兼容性，支持渐进式升级

> 详细请见 [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)

---

## 三、核心目录结构

```shell
spot_light/
├── hybrid_driver/      # 核心服务代码
├── scripts/            # 启动/管理/CLI 脚本
├── tests/              # 测试用例
├── config/             # 配置文件
├── requirements/       # 依赖管理
├── examples/           # 示例与演示
├── docs/               # 详细文档
├── start.sh            # 一键启动脚本
└── ...
```

---

## 四、快速上手

```shell
# 1. 安装依赖
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements/requirements.txt

# 2. 启动服务
./start.sh start

# 或者使用新的模块化API服务器
python hybrid_driver/start_api_server.py

# 3. 查看服务状态
./start.sh status

# 4. 使用 CLI 工具
./start.sh cli status

# 5. 运行测试
./start.sh test
```

### 执行器选择
系统支持两种执行器类型，可通过参数选择：
- **Selenium**: 适用于 WebView 操作（默认）
- **Appium**: 适用于原生应用和混合应用

```python
# 使用 Selenium 执行器（默认）
device = AndroidDevice(serial_id, executor_type="selenium")

# 使用 Appium 执行器
device = AndroidDevice(serial_id, executor_type="appium", 
                      appium_server_url="http://localhost:4723")
```

---

## 五、常用命令

| 命令                  | 说明               |
|----------------------|-------------------|
| ./start.sh start     | 启动服务           |
| ./start.sh stop      | 停止服务           |
| ./start.sh status    | 查看服务状态       |
| ./start.sh restart   | 重启服务           |
| ./start.sh logs      | 查看日志           |
| ./start.sh cli ...   | 运行 CLI 工具      |
| ./start.sh test      | 运行全部测试       |
| python hybrid_driver/start_api_server.py | 启动模块化API服务器 |
| python hybrid_driver/test_api.py | 测试API功能 |
| python hybrid_driver/migrate_api.py <目录> | 生成API迁移报告 |

---

## 六、文档导航

### 📚 详细文档（docs/）
- [📖 文档导航](docs/README.md) - 所有文档的导航入口
- [🏗️ 架构设计](docs/architecture/ARCHITECTURE.md) - 系统架构详解
- [🔌 API 文档](docs/api/API.md) - 完整API接口说明
- [📋 部署指南](docs/guides/DEPLOYMENT.md) - 部署和运维指南
- [🛠️ 开发工具](docs/guides/DEV_TOOLS_RECOMMEND.md) - 开发环境配置
- [📝 操作指令](docs/guides/Instruction.MD) - 操作指令系统说明
- [⚙️ 服务管理](docs/guides/SERVICE_MANAGEMENT.md) - 服务管理详细指南
- [🔄 协议映射](docs/guides/LEGACY_TO_NEW_PROTOCOL_MAPPING.md) - 新旧协议映射
- [📋 实施计划](docs/guides/IMPLEMENTATION_PLAN.md) - 项目实施计划
- [📊 数据采集](docs/guides/README.md) - 数据采集模块说明
- [❓ 常见问题](docs/guides/faq.md) - FAQ
- [📞 联系方式](docs/guides/contact.md) - 联系维护者

### 🔧 子模块文档
- [hybrid_driver/README.md](hybrid_driver/README.md) - 混合驱动服务详细说明
- [hybrid_driver/api/README.md](hybrid_driver/api/README.md) - API模块化设计文档

---

## 七、子模块说明

### hybrid_driver - 混合驱动服务

混合驱动服务是SpotLight平台的核心组件，提供设备管理、元素操作、页面管理、数据收集等功能。

#### 架构设计

采用模块化设计，将原来的单文件服务器拆分为多个功能模块：

```
hybrid_driver/api/
├── models.py          # 数据模型定义
├── utils.py           # 工具函数
├── config.py          # 配置管理
├── routers/           # 路由模块
│   ├── device.py      # 设备管理
│   ├── element.py     # 元素操作
│   ├── page.py        # 页面管理
│   ├── collect.py     # 数据收集
│   └── mock.py        # 模拟测试
└── README.md          # API文档
```

#### 功能模块

1. **设备管理** (`/device`)
   - 连接设备
   - 断开设备
   - 执行设备操作

2. **元素操作** (`/element`)
   - 查找元素
   - 查找多个元素
   - 点击元素
   - 执行操作序列

3. **页面管理** (`/page`)
   - 检查页面状态
   - 页面类型检测

4. **数据收集** (`/collect`)
   - 收集页面元素信息

5. **模拟测试** (`/mock`)
   - 模拟点击操作
   - 模拟查找元素

#### API端点

| 功能 | 端点 | 说明 |
|------|------|------|
| 设备管理 | `POST /device/connect` | 连接设备 |
| | `POST /device/disconnect` | 断开设备 |
| | `POST /device/action` | 执行设备操作 |
| 元素操作 | `POST /element/find` | 查找单个元素 |
| | `POST /element/find_all` | 查找多个元素 |
| | `POST /element/click` | 点击元素 |
| | `POST /element/operations` | 执行操作序列 |
| 页面管理 | `POST /page/check` | 检查页面状态 |
| 数据收集 | `POST /collect/items` | 收集元素信息 |
| 模拟测试 | `POST /mock/click` | 模拟点击 |
| | `POST /mock/find_element` | 模拟查找元素 |
| 系统 | `GET /health` | 健康检查 |
| | `GET /` | 根路径 |

#### 使用示例

**启动服务**
```python
# 使用优化后的服务器
from hybrid_driver.server_optimized import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**连接设备**
```python
import requests

response = requests.post("http://localhost:8000/device/connect", json={
    "serial_id": "123.56.152.41:6529"
})
print(response.json())
```

**查找元素**
```python
response = requests.post("http://localhost:8000/element/find", json={
    "serial_id": "123.56.152.41:6529",
    "method": "css selector",
    "selector": ".my-class"
})
print(response.json())
```

#### 优化优势

1. **模块化设计**: 按功能分离，便于维护和扩展
2. **清晰的API结构**: 使用前缀路由，API路径更加清晰
3. **统一的错误处理**: 所有接口使用统一的响应格式
4. **完整的文档**: 自动生成API文档
5. **易于测试**: 每个模块可以独立测试

#### 迁移指南

从原来的 `server.py` 迁移到新的模块化结构：

| 旧API | 新API |
|-------|-------|
| `POST /connect` | `POST /device/connect` |
| `POST /disconnect` | `POST /device/disconnect` |
| `POST /find_element` | `POST /element/find` |
| `POST /find_elements` | `POST /element/find_all` |
| `POST /click` | `POST /element/click` |
| `POST /run_operations` | `POST /element/operations` |
| `POST /check_page` | `POST /page/check` |
| `POST /collect_items` | `POST /collect/items` |
| `POST /mock_click` | `POST /mock/click` |
| `POST /mock_find_element` | `POST /mock/find_element` |

详细文档请参考：[hybrid_driver/api/README.md](hybrid_driver/api/README.md)

---

## 八、贡献与开发

- 贡献指南、代码规范、分支管理等（可补充 CONTRIBUTING.md）

---

## 九、FAQ & 联系方式

- [常见问题](docs/guides/faq.md)
- [联系方式](docs/guides/contact.md)

---

## 压测说明

## 目录结构
- `hybrid_driver/`：主服务代码
- `hybrid_driver/load_test/`：压测相关代码与数据
- `locustfile.py`、`locust_results.csv`：已迁移至 `hybrid_driver/load_test/`

## 压测方法

### 1. 运行压测

```bash
cd hybrid_driver/load_test
locust -f locustfile.py
```
- 浏览器访问 http://127.0.0.1:8089
- 配置并发用户数（如 100）、spawn rate、Host（如 http://127.0.0.1:8002）
- 点击 START 开始压测

### 2. 查看与分析压测结果
- 测试结束后，自动生成 `locust_results.csv`，包含每次请求的响应时间、服务端耗时、模拟耗时、额外延迟等
- 推荐用 Excel 或 pandas 分析：
  - 关注 `extra_delay` 字段，评估服务器调度/排队/网络延迟
  - 参考分析脚本 `analyze_locust.py`（可选）
- 可视化建议：用 matplotlib 画出 `extra_delay` 分布

### 3. 主要性能指标解读
- **response_time**：客户端观测到的总响应时间
- **process_time**：服务端真实处理耗时
- **mock_delay**：模拟的 sleep 时间
- **extra_delay**：response_time - process_time，反映非业务延迟

## 接口异步编写规范

- 所有 FastAPI 路由必须使用 `async def` 实现
- 所有阻塞型操作（如 Selenium、同步 I/O）必须用 `await run_sync(...)` 包裹，避免阻塞事件循环
- 纯异步 I/O 可直接用 `await`
- 线程池大小可通过如下方式调整（建议放在 main.py/server.py 顶部）：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=20)
asyncio.get_event_loop().set_default_executor(executor)
```

## 工具依赖与使用

- 依赖：`locust`, `pandas`, `matplotlib`（分析用）
- 安装依赖：
  ```bash
  pip install locust pandas matplotlib
  ```
- 主要压测脚本：`hybrid_driver/load_test/locustfile.py`
- 结果分析脚本（可选）：`analyze_locust.py`

---
如需进一步分析、可视化或性能调优建议，请参考本 README 或联系开发者。

> 📖 **文档说明**：所有详细文档已统一整理到 `docs/` 目录，主目录只保留项目入口和导航。如需查看详细内容，请访问对应的文档链接。

## 最新更新 (2024年)

### 架构优化
- ✅ **执行器工厂模式**: 引入 `ExecutorFactory` 统一管理执行器
- ✅ **类型安全**: 统一 `WebExecutor` 接口，修复类型注解
- ✅ **代码清理**: 移除冗余的 `web_driver_decorator` 代码
- ✅ **向后兼容**: 保持现有 API 兼容性

### API模块化重构
- ✅ **模块化设计**: 将620行的单文件 `server.py` 拆分为多个功能模块
- ✅ **路由优化**: 使用前缀路由（`/device/`, `/element/`, `/page/`, `/collect/`, `/mock/`）
- ✅ **代码组织**: 按功能分离为设备管理、元素操作、页面管理、数据收集、模拟测试
- ✅ **维护性提升**: 每个模块职责单一，便于定位和修改
- ✅ **扩展性增强**: 新增功能只需添加新的路由模块，不影响现有代码
- ✅ **迁移工具**: 提供完整的迁移工具和文档，支持从旧API平滑迁移

### 使用方式
```python
# 推荐：使用工厂模式
device = AndroidDevice(serial_id, executor_type="selenium")
device = AndroidDevice(serial_id, executor_type="appium")

# 直接使用工厂
executor = executor_factory.get_executor("selenium")
```

详细变更请参考 [架构文档](docs/architecture/ARCHITECTURE.md#最新架构改进-2024年)。

## 异步接口及异步方法编写规范

1. **FastAPI 路由必须使用 `async def`**
   - 保证接口异步，支持高并发。
   - 示例：
     ```python
     @app.post("/api")
     async def api_handler(req: RequestModel):
         ...
     ```

2. **纯异步 I/O 直接使用 `await`**
   - 如数据库异步驱动、httpx.AsyncClient、asyncio.sleep 等。
   - 示例：
     ```python
     await asyncio.sleep(1)
     resp = await async_client.get(url)
     ```

3. **阻塞型操作必须用 `await run_sync(...)` 或 `run_in_executor` 包裹**
   - 如 Selenium、同步 I/O、CPU 密集型任务。
   - 示例：
     ```python
     from hybrid_driver.utils.async_utils import run_sync
     result = await run_sync(blocking_func, arg1, arg2)
     ```
   - 或者：
     ```python
     loop = asyncio.get_event_loop()
     result = await loop.run_in_executor(None, blocking_func, arg1, arg2)
     ```

4. **线程池调整方法**
   - 可在 main.py/server.py 顶部设置全局线程池：
     ```python
     import asyncio
     from concurrent.futures import ThreadPoolExecutor
     executor = ThreadPoolExecutor(max_workers=20)
     asyncio.get_event_loop().set_default_executor(executor)
     ```
   - 线程池大小建议根据阻塞任务并发量和服务器资源调整。

5. **典型异步接口代码模板**
   ```python
   @app.post("/example", response_model=APIResponse)
   async def example(req: ExampleRequest):
       # 纯异步 I/O
       await asyncio.sleep(1)
       # 阻塞操作
       result = await run_sync(blocking_func, req.param)
       return APIResponse(code=0, message="success", data=result)
   ```

---

# Selenium Grid 4 Relay + Appium + Android WebView 自动化集群方案

## 目录结构

```
mini/
├── docker-compose.yml
├── node-android-relay/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── .dockerignore
```

## 一、快速启动

1. 构建 node-android-relay 镜像

```bash
cd node-android-relay
sudo docker build -t node-android-relay:latest .
```

2. 启动集群（可通过 --scale 动态扩容 node-android）

```bash
cd ..
sudo docker-compose up -d --scale node-android=2
```

3. 环境变量说明（每个 node-android 可单独指定）
- `SERIAL_ID`：目标 Android 设备的 adb 地址（如 192.168.1.100:5555）
- `BROWSER_VERSION`：WebView/Chrome 版本（如 128.0.6613.88）
- `DEVICE_NAME`：设备名（如 Pixel_5）
- `APPIUM_LOG_LEVEL`：Appium 日志级别（默认 debug）

4. 业务端 capabilities 示例

```python
capabilities = {
    "platformName": "Android",
    "appium:automationName": "UiAutomator2",
    "appium:deviceName": "Pixel_5",
    "appium:udid": "192.168.1.100:5555",
    "browserName": "chrome",
    "browserVersion": "128.0.6613.88"
}
```

- 连接 Hub 地址：`http://<宿主机IP>:4444/wd/hub`
- Hub 会根据能力自动分配到合适的 node-android 容器

5. 扩容/缩容/复用
- 通过 `docker-compose up -d --scale node-android=N` 动态扩容/缩容
- 每个 node-android 容器 session 结束后自动释放，可复用

## 二、注意事项
- 每个 node-android 容器建议只连一个设备，能力参数需与实际设备/浏览器版本一致
- chromedriver 版本需与 WebView/Chrome 严格匹配（可在 Dockerfile 或运行时自动下载/覆盖）
- 容器需有权限访问 /dev/bus/usb（物理设备）或 adb 端口（远程设备）

## 三、能力声明与调度
- node-android 容器通过 node.toml 动态声明能力，Hub 能力调度精准
- 支持多种能力参数扩展，如 platformVersion、automationName 等

## 四、常见问题排查
- node 未注册到 Hub：检查网络、端口、环境变量、Appium/adb 启动日志
- 设备未连接：检查 adb devices、物理连接或远程端口
- chromedriver 版本不匹配：需与 WebView/Chrome 版本严格一致

---
如需多版本 chromedriver 自动管理、K8s 部署、CI/CD 集成等高级方案，请联系维护者。
