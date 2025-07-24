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

# 示例：写入启动日志
cat > /opt/scripts/logs/startup.log << EOF
启动时间: $(date)
运行模式: ${CUSTOM_MODE:-默认模式}
超时时间: ${CUSTOM_TIMEOUT} 秒
日志级别: ${CUSTOM_LOG_LEVEL}
容器ID: $(hostname)
进程ID: $$
父进程ID: $PPID
执行阶段: 自定义启动脚本
EOF

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

echo ""
echo "=== 自定义启动脚本执行完成 ==="
echo "脚本完成时间: $(date)"
echo "即将启动 Selenium 服务..."
echo ""

# 脚本执行完成，继续启动 Selenium 服务
# 注意：这里不会执行任何命令，因为会被 custom-entrypoint.sh 中的 exec 调用 