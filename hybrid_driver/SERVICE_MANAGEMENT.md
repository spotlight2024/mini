# Spot Light 服务管理指南

本文档介绍如何在云服务器上使用 `nohup` 后台运行 Spot Light 服务，并提供完整的日志管理方案。

## 目录结构

```
hybrid_driver/
├── shell/                    # 服务管理脚本
│   ├── start_service.sh      # 启动服务
│   ├── stop_service.sh       # 停止服务
│   ├── status.sh            # 查看状态
│   ├── restart_service.sh    # 重启服务
│   └── view_logs.sh         # 日志查看
├── logs/                     # 日志目录
├── main.py                   # 主程序
├── server.py                 # 服务程序
├── start.sh                  # 便捷管理脚本
└── SERVICE_MANAGEMENT.md     # 本文档
```

## 🚀 快速使用（推荐）

使用便捷脚本，一个命令搞定所有操作：

```bash
# 给脚本添加执行权限
chmod +x start.sh shell/*.sh

# 启动服务
./start.sh start

# 查看状态
./start.sh status

# 实时查看日志
./start.sh logs

# 查看错误日志
./start.sh logs -e

# 停止服务
./start.sh stop

# 重启服务
./start.sh restart

# 查看帮助
./start.sh help
```

## 详细使用说明

### 1. 环境准备

确保服务器已安装 Python 3.7+ 和必要的依赖：

```bash
# 安装依赖
pip install -r requirements.txt

# 给脚本添加执行权限
chmod +x start.sh shell/*.sh
```

### 2. 启动服务

```bash
# 使用便捷脚本
./start.sh start

# 或直接使用shell脚本
./shell/start_service.sh
```

启动成功后会显示：
- 服务PID
- 日志文件路径
- 常用命令提示

### 3. 查看服务状态

```bash
# 使用便捷脚本
./start.sh status

# 或直接使用shell脚本
./shell/status.sh
```

显示服务运行状态、资源使用情况和端口监听状态。

### 4. 查看日志

```bash
# 使用便捷脚本
./start.sh logs          # 实时跟踪日志
./start.sh logs -l       # 查看最新日志
./start.sh logs -e       # 查看错误日志
./start.sh logs -t       # 查看今天的日志
./start.sh logs -a       # 查看所有日志文件

# 或直接使用shell脚本
./shell/view_logs.sh -f  # 实时跟踪日志
./shell/view_logs.sh -l  # 查看最新日志的最后100行
./shell/view_logs.sh -e  # 查看错误日志
./shell/view_logs.sh -t  # 查看今天的日志
./shell/view_logs.sh -a  # 查看所有日志文件
```

### 5. 停止服务

```bash
# 使用便捷脚本
./start.sh stop

# 或直接使用shell脚本
./shell/stop_service.sh
```

### 6. 重启服务

```bash
# 使用便捷脚本
./start.sh restart

# 或直接使用shell脚本
./shell/restart_service.sh
```

## 手动使用 nohup

如果您想手动使用 `nohup` 命令：

### 启动服务

```bash
# 基本启动
nohup python main.py > logs/service.log 2>&1 &

# 指定端口启动
nohup python main.py --port 8000 > logs/service.log 2>&1 &

# 后台运行并保存PID
nohup python main.py > logs/service.log 2>&1 & echo $! > logs/service.pid
```

### 查看日志

```bash
# 实时查看日志
tail -f logs/service.log

# 查看最后100行
tail -n 100 logs/service.log

# 查看错误日志
grep -i "error\|exception" logs/service.log
```

### 停止服务

```bash
# 如果有PID文件
kill $(cat logs/service.pid)

# 或者查找进程并停止
ps aux | grep "python main.py"
kill <PID>
```

## 日志管理

### 日志文件结构

```
logs/
├── service_20241201_143022.log    # 服务日志（带时间戳）
├── service.pid                    # 进程PID文件
├── spot_light_2024-12-01.log      # 应用日志（loguru生成）
├── error_20241201_143022.log      # 错误日志
├── selenium_20241201_143022.log   # Selenium相关日志
└── third_party_20241201_143022.log # 第三方库日志
```

### 日志轮转

- 日志文件大小超过 10MB 时自动轮转
- 保留 1 周的日志文件
- 自动压缩旧日志文件

### 日志级别

- **INFO**: 一般信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **DEBUG**: 调试信息（开发环境）

## 系统服务配置（可选）

如果您希望将服务配置为系统服务，可以创建 systemd 服务文件：

### 创建服务文件

```bash
sudo nano /etc/systemd/system/spot-light.service
```

```ini
[Unit]
Description=Spot Light Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/spot_light/hybrid_driver
ExecStart=/usr/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 启用服务

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable spot-light

# 启动服务
sudo systemctl start spot-light

# 查看状态
sudo systemctl status spot-light

# 查看日志
sudo journalctl -u spot-light -f
```

## 监控和维护

### 健康检查

```bash
# 检查服务是否响应
curl http://localhost:8000/docs

# 检查端口是否监听
netstat -tlnp | grep :8000
```

### 性能监控

```bash
# 查看进程资源使用
ps aux | grep "python main.py"

# 查看内存使用
top -p $(cat logs/service.pid)

# 查看网络连接
netstat -an | grep :8000
```

### 日志清理

```bash
# 清理7天前的日志
find logs/ -name "*.log" -mtime +7 -delete

# 清理压缩的日志文件
find logs/ -name "*.zip" -mtime +30 -delete
```

## 故障排除

### 常见问题

1. **服务启动失败**
   - 检查端口是否被占用：`lsof -i :8000`
   - 检查Python环境：`python --version`
   - 检查依赖：`pip list | grep fastapi`

2. **日志文件过大**
   - 检查日志轮转配置
   - 手动清理旧日志文件
   - 调整日志级别

3. **服务意外停止**
   - 检查系统资源使用情况
   - 查看错误日志：`./start.sh logs -e`
   - 检查系统日志：`journalctl -xe`

### 调试模式

```bash
# 前台运行（调试模式）
python main.py

# 启用详细日志
export LOG_LEVEL=DEBUG
python main.py
```

## 安全建议

1. **防火墙配置**
   ```bash
   # 只允许特定IP访问
   sudo ufw allow from 192.168.1.0/24 to any port 8000
   ```

2. **用户权限**
   - 使用非root用户运行服务
   - 限制日志目录权限

3. **SSL/TLS**
   - 在生产环境中使用HTTPS
   - 配置SSL证书

## 联系支持

如果遇到问题，请：
1. 查看日志文件获取详细错误信息
2. 检查系统资源使用情况
3. 确认网络和防火墙配置
4. 联系技术支持团队 