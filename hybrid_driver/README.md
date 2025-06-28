# hybrid_driver 子模块说明

本目录为 SpotLight 混合驱动服务核心模块，负责 Android 虚拟机自动化的 WebDriver 管理、设备池、操作指令等核心能力。

## 功能定位
- 提供统一的 WebDriver（Selenium/Appium）自动化能力
- 支持多设备并发、设备池管理
- 支持智能操作指令、弹窗处理、数据采集
- 对接主服务 API，支撑云端自动化

## 主要接口
- FastAPI 服务入口：`server.py`
- 设备池管理：`device_pool.py`
- 设备抽象：`device/android_device.py`
- WebDriver 实现：`webdriver/`
- 操作指令系统：`operation.py`

## 开发与测试
- 入口脚本：`main.py`（开发/调试）
- 服务管理脚本：见 `../scripts/service/`
- 单元/集成测试：见 `../tests/`
- 日志与配置：见 `../config/`

## 详细文档
- [主项目 README](../README.md)
- [架构设计](../docs/architecture/ARCHITECTURE.md)
- [API 文档](../docs/api/API.md)
- [服务管理指南](../docs/guides/SERVICE_MANAGEMENT.md)
- [操作指令说明](../docs/guides/Instruction.MD)
- [部署指南](../docs/guides/DEPLOYMENT.md)
- [开发工具推荐](../docs/guides/DEV_TOOLS_RECOMMEND.md)
- [文档导航](../docs/README.md)

如需详细开发、测试、接口说明，请参考主项目文档。 