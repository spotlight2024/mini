#!/bin/bash

# 自定义启动脚本示例
# 此脚本将在容器启动时执行，并可以接收外部传入的参数

set -e

echo "=== 自定义启动脚本开始执行 ==="
echo "脚本执行时间: $(date)"
echo "当前工作目录: $(pwd)"
echo "用户: $(whoami)"
echo "进程ID: $$"
echo "父进程ID: $PPID"

# 显示所有传入的参数
echo "传入的参数数量: $#"
echo "传入的参数列表:"
for i in "$@"; do
    echo "  - $i"
done

# 解析参数示例
CUSTOM_MODE=""
CUSTOM_TIMEOUT="30"
CUSTOM_LOG_LEVEL="INFO"

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            CUSTOM_MODE="$2"
            shift 2
            ;;
        --timeout)
            CUSTOM_TIMEOUT="$2"
            shift 2
            ;;
        --log-level)
            CUSTOM_LOG_LEVEL="$2"
            shift 2
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --mode <模式>        设置运行模式"
            echo "  --timeout <秒数>     设置超时时间"
            echo "  --log-level <级别>   设置日志级别"
            echo "  --help               显示此帮助信息"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 显示解析后的参数
echo ""
echo "=== 解析后的参数 ==="
echo "运行模式: ${CUSTOM_MODE:-默认模式}"
echo "超时时间: ${CUSTOM_TIMEOUT} 秒"
echo "日志级别: ${CUSTOM_LOG_LEVEL}"

# 执行自定义逻辑
echo ""
echo "=== 执行自定义逻辑 ==="

# 示例：设置环境变量
export CUSTOM_MODE="$CUSTOM_MODE"
export CUSTOM_TIMEOUT="$CUSTOM_TIMEOUT"
export CUSTOM_LOG_LEVEL="$CUSTOM_LOG_LEVEL"

# 示例：创建日志目录
mkdir -p /opt/scripts/logs

# 示例：输出启动信息到控制台
echo "=== 启动信息 ==="
echo "启动时间: $(date)"
echo "运行模式: ${CUSTOM_MODE:-默认模式}"
echo "超时时间: ${CUSTOM_TIMEOUT} 秒"
echo "日志级别: ${CUSTOM_LOG_LEVEL}"
echo "容器ID: $(hostname)"
echo "进程ID: $$"
echo "父进程ID: $PPID"
echo "执行阶段: 自定义启动脚本"
echo "=================="

# 示例：根据模式执行不同的初始化
case "${CUSTOM_MODE}" in
    "debug")
        echo "调试模式：启用详细日志"
        export SELENIUM_LOG_LEVEL="DEBUG"
        ;;
    "production")
        echo "生产模式：优化性能设置"
        export SELENIUM_LOG_LEVEL="WARN"
        ;;
    "test")
        echo "测试模式：启用测试配置"
        export SELENIUM_LOG_LEVEL="INFO"
        ;;
    *)
        echo "默认模式：使用标准配置"
        export SELENIUM_LOG_LEVEL="INFO"
        ;;
esac

# 示例：检查必要的目录和权限
echo "检查系统状态..."
if [ -d "/opt/scripts" ]; then
    echo "✓ 脚本目录存在"
else
    echo "✗ 脚本目录不存在"
fi

if [ -w "/opt/scripts/logs" ]; then
    echo "✓ 日志目录可写"
else
    echo "✗ 日志目录不可写"
fi

# # 初始化 ADB 服务
# echo ""
# echo "=== 初始化 ADB 服务 ==="
# if [ -f /opt/custom-scripts/adb_init.sh ]; then
#     echo "执行 ADB 初始化脚本..."
#     /opt/custom-scripts/adb_init.sh
#     echo "ADB 初始化完成"
# else
#     echo "警告: ADB 初始化脚本不存在"
# fi

# # 显示 ADB 设备状态
# echo "当前 ADB 设备状态:"
# adb devices

# 启动 ADB 代理服务
echo ""
echo "=== 启动 ADB 代理服务 ==="

# 首先启动真实的 ADB 服务在 5038 端口
echo "启动真实 ADB 服务在 5038 端口..."
adb -P 5038 start-server
echo "ADB 服务已启动在端口 5038"

if [ -f /opt/custom-scripts/adb_proxy.py ]; then
    echo "启动 ADB 代理服务在 5037 端口..."
    
    # 检查Python环境
    echo "检查Python环境..."
    python3 --version
    which python3
    
    # 检查脚本权限
    echo "检查脚本权限..."
    ls -la /opt/custom-scripts/adb_proxy.py
    
    # 确保日志目录存在并有正确权限
    echo "确保日志目录权限..."
    mkdir -p /opt/scripts/logs
    chmod 755 /opt/scripts/logs
    
    # 在后台启动代理服务
    echo "启动代理服务..."
    nohup python3 /opt/custom-scripts/adb_proxy.py &
    ADB_PROXY_PID=$!
    echo "ADB 代理服务已启动，PID: $ADB_PROXY_PID"
    
    # 等待代理服务启动
    sleep 3
    
    # 检查代理服务是否正常运行
    if ps -p $ADB_PROXY_PID > /dev/null; then
        echo "✓ ADB 代理服务运行正常"
        # 将PID保存到文件，以便后续管理
        echo $ADB_PROXY_PID > /opt/scripts/adb_proxy.pid
        
        # 测试代理连接
        echo "测试代理连接..."
        if nc -z localhost 5037; then
            echo "✓ 代理服务监听端口 5037 正常"
        else
            echo "✗ 代理服务监听端口 5037 失败"
        fi
    else
        echo "✗ ADB 代理服务启动失败"
        echo "检查代理服务进程状态..."
        ps aux | grep adb_proxy
    fi
else
    echo "警告: ADB 代理脚本不存在: /opt/custom-scripts/adb_proxy.py"
fi

# 显示 ADB 设备状态
echo "当前 ADB 设备状态:"
adb devices

echo ""
echo "=== 自定义启动脚本执行完成 ==="
echo "脚本完成时间: $(date)"
echo "即将启动 Selenium 服务..."
echo ""

# 脚本执行完成，继续启动 Selenium 服务
# 注意：这里不会执行任何命令，因为会被 custom-entrypoint.sh 中的 exec 调用 