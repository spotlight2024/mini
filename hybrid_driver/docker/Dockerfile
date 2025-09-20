# 轻量级 SpotLight Hybrid Driver API 容器
FROM python:3.10-slim

# 设置时区为Asia/Shanghai
ENV TZ=Asia/Shanghai

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=10001
ENV PIP_TIMEOUT=300
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 使用国内镜像源安装基础依赖
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    make \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 创建时区链接
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 设置工作目录
WORKDIR /app

# 升级 pip 并设置超时
RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目文件
COPY hybrid_driver/ ./hybrid_driver/

# 复制 requirements 文件
COPY hybrid_driver/requirements.txt ./

# 安装依赖集，使用国内镜像源
RUN pip install --no-cache-dir --timeout=300 -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 创建非 root 用户
RUN useradd -m -u 1000 spotlight

# 创建必要的目录并设置权限
RUN mkdir -p logs data cache && \
    chown -R spotlight:spotlight /app

USER spotlight

# 暴露端口
EXPOSE 10001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10001/health || exit 1

# 启动命令
CMD ["python", "hybrid_driver/start_api_server.py", "--host", "0.0.0.0", "--port", "10001"]