# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 只复制 requirements.txt
COPY requirements.txt /app/requirements.txt

# 安装依赖
RUN pip install --no-cache-dir -r /app/requirements.txt

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "hybrid_driver/start_api_server.py", "--host", "0.0.0.0", "--port", "8000"] 