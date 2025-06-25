# Spot Light Hybrid Driver

Spot Light 混合驱动服务，支持 Web 和移动端自动化操作。

## 项目结构

```
hybrid_driver/
├── shell/                    # 服务管理脚本
│   ├── start_service.sh      # 启动服务
│   ├── stop_service.sh       # 停止服务
│   ├── status.sh            # 查看状态
│   ├── restart_service.sh    # 重启服务
│   └── view_logs.sh         # 日志查看
├── logs/                     # 日志目录
├── main.py                   # 主程序入口
├── server.py                 # FastAPI 服务
├── start.sh                  # 便捷管理脚本
├── SERVICE_MANAGEMENT.md     # 详细服务管理文档
└── README.md                 # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 给脚本添加执行权限
chmod +x start.sh shell/*.sh

# 启动服务
./start.sh start
```

### 3. 查看状态

```bash
./start.sh status
```

### 4. 查看日志

```bash
./start.sh logs          # 实时跟踪日志
./start.sh logs -e       # 查看错误日志
```

### 5. 停止服务

```bash
./start.sh stop
```

## 便捷命令

```bash
./start.sh start         # 启动服务
./start.sh stop          # 停止服务
./start.sh restart       # 重启服务
./start.sh status        # 查看状态
./start.sh logs          # 实时查看日志
./start.sh logs -e       # 查看错误日志
./start.sh logs -l       # 查看最新日志
./start.sh logs -t       # 查看今天的日志
./start.sh help          # 查看帮助
```

## API 文档

服务启动后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 详细文档

更多详细信息请参考：
- [服务管理指南](SERVICE_MANAGEMENT.md) - 完整的服务管理说明
- [API 文档](../API.md) - API 接口说明
- [架构文档](../ARCHITECTURE.md) - 系统架构说明

## 开发

### 调试模式

```bash
# 前台运行（调试模式）
python main.py

# 启用详细日志
export LOG_LEVEL=DEBUG
python main.py
```

### 测试

```bash
# 运行测试
pytest

# 运行特定测试
pytest tests/test_device.py
``` 