# 自定义Chrome节点镜像 - tinyproxy透明代理架构
FROM selenium/node-chrome:138.0.7204.157-chromedriver-138.0.7204.157-grid-4.34.0-20250717

USER root

# 安装tinyproxy和必要工具 (轻量级代理方案)
RUN apt-get update && apt-get install -y \
    tinyproxy \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# 配置sudo无密码权限
RUN echo "seluser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# 创建必要目录
RUN mkdir -p /opt/tinyproxy-setup /var/log/tinyproxy

# 复制tinyproxy配置和脚本
COPY tinyproxy.conf.template /opt/tinyproxy-setup/
COPY setup-tinyproxy.sh /opt/tinyproxy-setup/
COPY custom-entrypoint.sh /opt/tinyproxy-setup/

# 设置执行权限
RUN chmod +x /opt/tinyproxy-setup/*.sh

# 创建tinyproxy运行目录和权限
RUN mkdir -p /var/run/tinyproxy && \
    chown nobody:nogroup /var/run/tinyproxy /var/log/tinyproxy

# 切换回selenium用户
USER 1200

# 使用自定义入口点，但保留原始能力
ENTRYPOINT ["/opt/tinyproxy-setup/custom-entrypoint.sh"]