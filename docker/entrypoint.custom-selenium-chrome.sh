#!/bin/bash
set -e

echo "=== 自定义 Selenium Chrome 容器启动 ==="
echo "容器启动时间: $(date)"
echo "当前进程ID: $$"
echo "传入的参数: $@"
echo "执行阶段: 1. 自定义启动脚本包装器开始"

echo "# EXTRA_LIBS 环境变量检查"
if [ -n "${EXTRA_LIBS}" ]; then
  echo "local : Classpath will be enriched with these external jars : ${EXTRA_LIBS}"
else
  echo "local :EXTRA_LIBS is not set or empty"
fi

# 执行自定义启动脚本，并传递所有参数
if [ -f /opt/custom-scripts/custom_startup.sh ]; then
    echo "执行阶段: 2. 调用自定义启动脚本..."
    /opt/custom-scripts/custom_startup.sh "$@"
    echo "执行阶段: 3. 自定义启动脚本执行完成"
else
    echo "警告: 自定义启动脚本不存在: /opt/custom-scripts/custom_startup.sh"
fi

echo "执行阶段: 4. 启动原始 Selenium Chrome 服务..."
echo "即将执行: exec /opt/bin/entry_point.sh $@"
echo "注意: exec 将替换当前进程，后续日志将由 Selenium 服务输出"
exec /opt/bin/entry_point.sh "$@" 