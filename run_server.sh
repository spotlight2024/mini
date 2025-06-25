#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 设置Python路径
export PYTHONPATH=/root/script/mini:$PYTHONPATH

echo "启动 hybrid_driver 服务器..."
echo "Python路径: $PYTHONPATH"
echo "当前目录: $(pwd)"

# 运行服务器
python3 hybrid_driver/server.py 