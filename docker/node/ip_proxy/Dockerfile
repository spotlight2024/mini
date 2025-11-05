# Chrome节点镜像 - 保留业务逻辑，代理由sidecar处理
FROM selenium/node-chrome:138.0.7204.183-chromedriver-138.0.7204.183-grid-4.38.0-20251101

USER root

# 设置时区为中国上海时间
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装必要工具 (保留您的业务逻辑需求)
RUN apt-get update && apt-get install -y \
    curl \
    sudo \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 配置sudo无密码权限 (保留业务逻辑)
RUN echo "seluser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# 创建必要目录 (保留业务逻辑)
RUN mkdir -p /opt/node-setup

# 复制业务逻辑脚本和sidecar相关脚本
COPY custom-entrypoint.sh /opt/node-setup/
COPY tinyproxy-sidecar.sh /opt/node-setup/
COPY switch-proxy.sh /opt/node-setup/

# 复制修改后的selenium JAR包，替换原始版本
COPY selenium_server_deploy.jar /opt/selenium/selenium-server.jar

# 设置执行权限
RUN chmod +x /opt/node-setup/*.sh

# 切换回selenium用户
USER 1200

# 使用自定义入口点 (保留业务逻辑)
ENTRYPOINT ["/opt/node-setup/custom-entrypoint.sh"]
