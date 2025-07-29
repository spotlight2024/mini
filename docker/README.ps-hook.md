# ADB 代理 PS 命令 Hook 功能

## 功能概述

ADB代理现在支持自动hook `ps && ps -A` 命令，在其后面自动添加 `| grep 'u10_'` 过滤条件，只返回包含 `u10_` 的进程信息。

## 工作原理

### ADB协议格式
ADB协议使用以下格式：`长度+命令`
- 长度：4位十六进制数，表示命令部分的字符数
- 命令：实际的shell命令

### 原始命令
```
0011shell:ps && ps -A
```
- `0011`：长度字段（17个字符）
- `shell:ps && ps -A`：命令部分

### Hook后的命令
```
0020shell:ps && ps -A | grep 'u10_'
```
- `0020`：新的长度字段（32个字符）
- `shell:ps && ps -A | grep 'u10_'`：修改后的命令

## 功能特点

1. **自动检测**：自动识别包含 `ps && ps -A` 的ADB shell命令
2. **智能替换**：只修改匹配的命令，其他命令保持不变
3. **长度计算**：自动重新计算并更新ADB协议的长度字段
4. **日志记录**：在INFO级别记录hook过程和长度变化
5. **错误处理**：包含完整的异常处理机制

## 日志输出示例

### 检测到目标命令时
```
🔍 检测到ps命令: 0011shell:ps && ps -A
📏 原始长度: 17 (0x0011)
📏 新长度: 32 (0x0020)
✅ 修改后的命令: 0020shell:ps && ps -A | grep 'u10_'
```

### 其他命令（DEBUG级别）
```
📝 原始请求: 0011shell:echo "hello"
```

## 支持的命令模式

### ✅ 会被Hook的命令
- `ps && ps -A`
- `ps && ps -A && echo "test"`
- `ps && ps -A | grep something`

### ❌ 不会被Hook的命令
- `ps -A`（不包含 `ps &&`）
- `ps`（不包含 `&& ps -A`）
- `echo "hello"`
- 其他任何不包含 `ps && ps -A` 的命令

## 使用方法

### 1. 启动容器
```bash
# 使用默认配置启动
docker compose up chrome-driver

# 或者使用自定义日志级别
docker run -e ADB_PROXY_LOG_LEVEL=INFO custom-selenium-chrome:adb_1
```

### 2. 通过ADB连接
```bash
# 连接到代理端口
adb connect localhost:5037

# 执行ps命令（会被自动hook）
adb shell "ps && ps -A"
```

### 3. 查看日志
```bash
# 查看容器日志
docker logs chrome-driver

# 或者实时查看
docker logs -f chrome-driver
```

## 测试功能

### 运行测试脚本
```bash
# 在容器内运行测试
docker exec -it chrome-driver python3 /opt/custom-scripts/test_hook.py
```

### 手动测试
```bash
# 连接到代理
adb connect localhost:5037

# 执行测试命令
adb shell "ps && ps -A"
```

## 配置选项

### 日志级别控制
```bash
# 查看详细hook过程
export ADB_PROXY_LOG_LEVEL=DEBUG

# 只查看重要信息
export ADB_PROXY_LOG_LEVEL=INFO

# 关闭hook日志（只保留错误）
export ADB_PROXY_LOG_LEVEL=WARNING
```

### Docker Compose 配置
```yaml
version: '3.8'
services:
  chrome-driver:
    build:
      context: .
      dockerfile: Dockerfile.custom-selenium-chrome
    environment:
      # 设置日志级别
      - ADB_PROXY_LOG_LEVEL=INFO
    ports:
      - "4444:4444"  # Selenium
      - "5037:5037"  # ADB Proxy
```

## 性能影响

### 最小影响
- Hook处理非常快速（字符串替换）
- 只在匹配特定命令时执行
- 其他命令直接通过，无额外处理

### 日志级别建议
- **生产环境**：使用 `WARNING` 或 `ERROR`
- **调试环境**：使用 `DEBUG` 查看详细信息
- **高性能场景**：使用 `NONE` 完全关闭日志

## 故障排除

### Hook不生效
1. 检查命令格式是否正确：`ps && ps -A`
2. 确认日志级别设置：使用 `DEBUG` 查看详细信息
3. 检查容器日志：`docker logs chrome-driver`

### 性能问题
1. 降低日志级别：`ADB_PROXY_LOG_LEVEL=WARNING`
2. 完全关闭日志：`ADB_PROXY_LOG_LEVEL=NONE`
3. 检查是否有其他性能瓶颈

### 日志过多
1. 提高日志级别：`ADB_PROXY_LOG_LEVEL=WARNING`
2. 只显示错误：`ADB_PROXY_LOG_LEVEL=ERROR`
3. 完全关闭：`ADB_PROXY_LOG_LEVEL=NONE`

## 扩展功能

### 添加更多Hook规则
可以在 `hook_ps_command` 函数中添加更多匹配规则：

```python
def hook_ps_command(data: bytes) -> bytes:
    try:
        str_data = data.decode('utf-8', errors='replace')
        
        # 现有的ps命令hook
        if 'ps && ps -A' in str_data:
            # ... 现有逻辑
        
        # 添加新的hook规则
        if 'your_command' in str_data:
            # ... 新的hook逻辑
        
    except Exception as e:
        logger.error(f"❌ hook_ps_command 异常: {e}")
    
    return data
```

### 自定义过滤条件
可以修改过滤条件来匹配不同的进程：

```python
# 修改过滤条件
new_str_data = str_data.replace('ps && ps -A', 'ps && ps -A | grep \'your_pattern\'')
```

## 注意事项

1. **命令格式**：Hook只匹配 `ps && ps -A` 格式
2. **大小写敏感**：命令匹配是大小写敏感的
3. **实时生效**：Hook在每次请求时实时处理
4. **不影响其他功能**：Hook不影响ADB代理的其他功能 