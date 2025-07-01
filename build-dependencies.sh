#!/bin/bash

set -e

echo "🔨 本地构建依赖镜像..."

# 构建Redis镜像
echo "🔨 构建Redis镜像..."
cat > Dockerfile.redis << 'EOF'
FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y redis-server && rm -rf /var/lib/apt/lists/*

EXPOSE 6379

CMD ["redis-server", "--appendonly", "yes"]
EOF

docker build -f Dockerfile.redis -t redis:alpine .
rm Dockerfile.redis

# 构建MongoDB镜像
echo "🔨 构建MongoDB镜像..."
cat > Dockerfile.mongo << 'EOF'
FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y wget gnupg && \
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add - && \
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
    apt-get update && apt-get install -y mongodb-org && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /data/db

EXPOSE 27017

CMD ["mongod", "--bind_ip_all"]
EOF

docker build -f Dockerfile.mongo -t mongo:latest .
rm Dockerfile.mongo

# 构建Selenium Hub镜像
echo "🔨 构建Selenium Hub镜像..."
cat > Dockerfile.selenium << 'EOF'
FROM openjdk:11-jre-slim

RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

# 下载Selenium Standalone Server
RUN wget -O /opt/selenium-server.jar https://github.com/SeleniumHQ/selenium/releases/download/selenium-4.15.0/selenium-server-4.15.0.jar

EXPOSE 4444

CMD ["java", "-jar", "/opt/selenium-server.jar", "hub"]
EOF

docker build -f Dockerfile.selenium -t selenium/hub:latest .
rm Dockerfile.selenium

echo "✅ 所有依赖镜像构建完成！" 