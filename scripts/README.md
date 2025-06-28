# Scripts 脚本工具目录

本目录包含 SpotLight 项目的所有脚本工具，按功能分类组织。

## 📁 目录结构

```
scripts/
├── service/          # 服务管理脚本
├── cli/              # 命令行工具
├── deployment/       # 部署脚本
├── utils/            # 实用工具脚本
└── README.md         # 本文档
```

## 🚀 服务管理脚本 (service/)

### 主要脚本
- `start_service.sh` - 启动服务
- `stop_service.sh` - 停止服务
- `status.sh` - 查看服务状态
- `restart_service.sh` - 重启服务
- `view_logs.sh` - 查看日志

### 使用方法
```bash
# 通过主启动脚本调用
./start.sh start      # 启动服务
./start.sh stop       # 停止服务
./start.sh status     # 查看状态
./start.sh restart    # 重启服务
./start.sh logs       # 查看日志

# 或直接调用
./scripts/service/start_service.sh
./scripts/service/stop_service.sh
```

## 🖥️ 命令行工具 (cli/)

### 主要工具
- `cli.py` - SpotLight CLI 工具

### 使用方法
```bash
# 通过主启动脚本调用
./start.sh cli status     # 查看服务状态
./start.sh cli connect    # 连接设备

# 或直接调用
python3 scripts/cli/cli.py status
python3 scripts/cli/cli.py connect --serial_id=xxx --ip=xxx --port=xxx
```

## 🚀 部署脚本 (deployment/)

### 功能
- 项目部署相关脚本
- 环境配置脚本
- 生产环境部署脚本

### 使用方法
```bash
# 待补充具体部署脚本
```

## 🛠️ 实用工具脚本 (utils/)

### 功能
- 环境检查脚本
- 配置备份脚本
- 日志清理脚本
- 其他实用工具

### 使用方法
```bash
# 待补充具体工具脚本
```

## 📋 主启动脚本

项目根目录的 `start.sh` 是统一入口，支持以下命令：

### 服务管理
```bash
./start.sh start      # 启动服务
./start.sh stop       # 停止服务
./start.sh status     # 查看状态
./start.sh restart    # 重启服务
./start.sh logs       # 查看日志
```

### 开发工具
```bash
./start.sh cli        # 运行CLI工具
./start.sh test       # 运行测试
./start.sh install    # 安装依赖
./start.sh clean      # 清理缓存
```

### 日志选项
```bash
./start.sh logs -f    # 实时跟踪日志
./start.sh logs -e    # 查看错误日志
./start.sh logs -t    # 查看今天的日志
./start.sh logs -a    # 查看所有日志文件
```

## 🔧 脚本开发规范

1. **命名规范**：使用小写字母和下划线
2. **权限设置**：确保脚本有执行权限 `chmod +x script.sh`
3. **错误处理**：添加适当的错误检查和退出码
4. **日志输出**：使用统一的日志格式和emoji图标
5. **帮助信息**：每个脚本都应包含帮助信息

## 📝 添加新脚本

1. 按功能分类放入对应目录
2. 更新本README文档
3. 如需要，更新主启动脚本 `start.sh`
4. 确保脚本有执行权限

---

更多信息请参考主项目文档或联系维护者。 