# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制 hybrid_driver 目录到容器
COPY hybrid_driver /app/hybrid_driver
# 复制 requirements.txt 到容器
COPY requirements.txt /app/requirements.txt

# 安装依赖
RUN pip install --no-cache-dir -r /app/requirements.txt

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "hybrid_driver/start_api_server.py", "--host", "0.0.0.0", "--port", "8000"] 