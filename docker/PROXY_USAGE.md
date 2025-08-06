# Chrome代理扩展使用说明

## 🚀 快速使用

### 1. 构建镜像
```bash
./build.sh --build-only
```

### 2. 启动服务
```bash
docker compose --env-file proxy.env up -d
```

### 3. 测试功能
```bash
./build.sh
```

## 📋 脚本说明

### build.sh - 构建脚本
- `./build.sh` - 构建镜像并测试
- `./build.sh --build-only` - 仅构建镜像
- `./build.sh --test-only` - 仅运行测试
- `./build.sh --start` - 构建并启动服务

### test.sh - 测试脚本
- 在容器中运行：`docker exec chrome-driver /opt/custom-scripts/test.sh`

## ⚙️ 配置

### 环境变量 (proxy.env)
```bash
PROXY_ENABLED=true
PROXY_HOST=61.132.231.167
PROXY_PORT=57001
PROXY_USERNAME=vgmpgv
PROXY_PASSWORD=1bk79g9y
```

### 命令行参数
```bash
./scripts/setup_proxy_config.sh \
    --host 61.132.231.167 \
    --port 57001 \
    --username vgmpgv \
    --password 1bk79g9y
```

## 🔍 验证

### 检查代理配置
```bash
docker exec chrome-driver cat /opt/chrome_extensions/proxy_auth/proxy_config.json
```

### 查看服务状态
```bash
docker compose ps
docker compose logs -f chrome-driver
```

## 📚 详细文档

- [README_PROXY.md](README_PROXY.md) - 完整使用指南
- [PROXY_SETUP.md](../docs/guides/PROXY_SETUP.md) - 详细技术说明
