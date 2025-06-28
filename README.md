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

> 📖 **文档说明**：所有详细文档已统一整理到 `docs/` 目录，主目录只保留项目入口和导航。如需查看详细内容，请访问对应的文档链接。
