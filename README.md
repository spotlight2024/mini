# SpotLight 混合驱动自动化平台

## 一、项目简介

SpotLight 是面向 Android 虚拟机自动化的云端混合驱动平台，支持微信小程序/WebView/原生自动化，具备多设备并发、智能指令、弹窗处理、数据采集等能力。

---

## 二、架构总览

```
用户指令 → Android虚拟机APP → 云服务器Script服务 → 混合WebDriver → 微信小程序/WebView
```
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

# 3. 查看服务状态
./start.sh status

# 4. 使用 CLI 工具
./start.sh cli status

# 5. 运行测试
./start.sh test
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

---

## 七、子模块说明

- [hybrid_driver/README.md](hybrid_driver/README.md)：混合驱动服务的详细说明、API、开发与测试方法等。

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
