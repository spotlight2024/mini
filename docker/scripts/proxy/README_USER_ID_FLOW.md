# UserId 动态传递流程说明

## 📋 概述

本系统实现了 Selenium 与 ADB 代理之间的 userId 动态传递机制，支持多用户容器环境下的安全隔离。

## 🔄 工作流程

### 1. Driver 连接阶段
```
Selenium Driver → 获取 userId → 保存到文件 → 启动清理线程
```

### 2. ADB 代理阶段
```
ADB 请求 → 读取文件 → 动态生成 grep → 修改 ps 命令
```

## 🏗️ 架构设计

### 文件结构
```
/tmp/
├── adb_proxy_user_id.txt    # userId 文件 (timestamp:userId)
└── adb_proxy_user_id.lock   # 锁文件 (防止并发冲突)
```

### 数据格式
- **新格式**: `timestamp:userId` (例如: `1703123456789:u10_123`)
- **旧格式**: `userId` (兼容性支持)

## ⚙️ 配置参数

### Selenium 配置
```java
// 在 capabilities 中设置
capabilities.setCapability("se:userId", "u10_123");
```

### ADB 代理配置
```python
# 环境变量
ADB_PROXY_LOG_LEVEL=INFO  # 日志级别

# 文件路径
USER_ID_FILE_PATH = '/tmp/adb_proxy_user_id.txt'
```

## 🔧 功能特性

### ✅ 健壮性设计
- **时间戳验证**: 自动检测过期文件
- **并发安全**: 使用锁文件防止冲突
- **错误处理**: 完善的异常处理和降级机制
- **自动清理**: 定期清理过期文件

### ✅ 多用户支持
- **用户隔离**: 每个用户独立的 userId
- **及时清理**: 30秒后自动清理文件
- **容器复用**: 支持容器被多个用户复用

### ✅ 兼容性
- **向后兼容**: 支持旧格式文件
- **格式容错**: 自动处理格式错误
- **降级机制**: 文件异常时使用默认值

## 📊 监控和日志

### 日志级别
```bash
# 设置日志级别
export ADB_PROXY_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, NONE
```

### 关键日志
```
[AdbSessionFactory] userId saved to file: u10_123 -> /tmp/adb_proxy_user_id.txt
[AdbSessionFactory] userId file cleaned up: u10_123
[adb_proxy] 📁 从文件读取到 userId: u10_123 (时间戳: 1703123456789)
[adb_proxy] ✅ 修改后的命令: 0011shell:ps && ps -A | grep 'u10_123'
```

## 🧪 测试

### 运行测试
```bash
# 基本测试
python3 test_user_id_flow.py

# 健壮性测试
python3 test_robust_user_id_flow.py
```

### 测试覆盖
- ✅ 基本文件读写
- ✅ 时间戳解析
- ✅ 并发访问
- ✅ 过期清理
- ✅ ps 命令修改
- ✅ 错误处理

## 🚀 部署指南

### 1. 更新 Selenium 代码
```bash
# 编译 Java 代码
cd selenium/java
./gradlew build
```

### 2. 启动 ADB 代理
```bash
# 启动代理
cd mini/docker/scripts/proxy
python3 adb_proxy.py
```

### 3. 配置环境
```bash
# 设置日志级别
export ADB_PROXY_LOG_LEVEL=INFO

# 确保文件权限
chmod 666 /tmp/adb_proxy_user_id.txt
```

## 🔍 故障排除

### 常见问题

#### 1. 文件权限问题
```bash
# 检查文件权限
ls -la /tmp/adb_proxy_user_id*

# 修复权限
chmod 666 /tmp/adb_proxy_user_id.txt
chmod 666 /tmp/adb_proxy_user_id.lock
```

#### 2. 文件过期问题
```bash
# 手动清理过期文件
rm -f /tmp/adb_proxy_user_id.txt
rm -f /tmp/adb_proxy_user_id.lock
```

#### 3. 日志调试
```bash
# 设置详细日志
export ADB_PROXY_LOG_LEVEL=DEBUG

# 重启代理
python3 adb_proxy.py
```

### 监控命令
```bash
# 查看文件状态
ls -la /tmp/adb_proxy_user_id*

# 查看文件内容
cat /tmp/adb_proxy_user_id.txt

# 监控日志
tail -f /var/log/adb_proxy.log
```

## 📈 性能优化

### 文件操作优化
- 使用内存缓存减少文件 I/O
- 批量处理文件操作
- 异步清理任务

### 并发优化
- 文件锁机制
- 读写分离
- 连接池管理

## 🔒 安全考虑

### 文件安全
- 临时文件权限控制
- 定期清理机制
- 内容验证

### 用户隔离
- userId 唯一性保证
- 会话隔离
- 资源清理

## 📝 更新日志

### v1.0.0 (2024-12-19)
- ✅ 基础 userId 传递功能
- ✅ 文件读写机制
- ✅ 基本错误处理

### v1.1.0 (2024-12-19)
- ✅ 时间戳支持
- ✅ 自动清理机制
- ✅ 并发安全
- ✅ 健壮性增强
- ✅ 兼容性支持

## 🤝 贡献指南

### 代码规范
- 遵循 PEP 8 (Python)
- 遵循 Google Java Style (Java)
- 添加适当的注释和文档

### 测试要求
- 新功能必须包含测试
- 保持测试覆盖率 > 80%
- 运行所有测试确保通过

---

*最后更新时间: 2024-12-19* 