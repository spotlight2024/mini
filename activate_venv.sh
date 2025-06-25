#!/bin/bash

# 激活虚拟环境脚本
echo "正在激活Python虚拟环境..."
source venv/bin/activate
echo "虚拟环境已激活！"
echo "现在可以使用以下命令："
echo "  - python main.py (运行主程序)"
echo "  - pip install <package> (安装新包)"
echo "  - deactivate (退出虚拟环境)"
echo ""
echo "当前Python路径: $(which python)"
echo "当前pip路径: $(which pip)" 