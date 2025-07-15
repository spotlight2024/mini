# SpotLight Hybrid Driver API

## 概述

这是SpotLight混合驱动自动化测试系统的API服务，采用模块化设计，提供设备管理、元素操作、页面管理、数据收集等功能。

## 架构设计

### 模块化结构

```
hybrid_driver/api/
├── __init__.py
├── models.py          # 数据模型定义
├── utils.py           # 工具函数
├── routers/           # 路由模块
│   ├── __init__.py
│   ├── device.py      # 设备管理
│   ├── element.py     # 元素操作
│   ├── page.py        # 页面管理
│   ├── collect.py     # 数据收集
│   └── mock.py        # 模拟测试
└── README.md          # 本文档
```

### 功能模块

1. **设备管理** (`/device`)
   - 连接设备
   - 断开设备
   - 执行设备操作

2. **元素操作** (`/element`)
   - 查找元素
   - 查找多个元素
   - 点击元素
   - 执行操作序列

3. **页面管理** (`/page`)
   - 检查页面状态
   - 页面类型检测

4. **数据收集** (`/collect`)
   - 收集页面元素信息

5. **模拟测试** (`/mock`)
   - 模拟点击操作
   - 模拟查找元素

## API端点

### 设备管理

- `POST /device/connect` - 连接设备
- `POST /device/disconnect` - 断开设备
- `POST /device/action` - 执行设备操作

### 元素操作

- `POST /element/find` - 查找单个元素
- `POST /element/find_all` - 查找多个元素
- `POST /element/click` - 点击元素
- `POST /element/operations` - 执行操作序列

### 页面管理

- `POST /page/check` - 检查页面状态

### 数据收集

- `POST /collect/items` - 收集元素信息

### 模拟测试

- `POST /mock/click` - 模拟点击
- `POST /mock/find_element` - 模拟查找元素

### 系统

- `GET /health` - 健康检查
- `GET /` - 根路径

## 使用示例

### 启动服务

```python
# 使用优化后的服务器
from hybrid_driver.server_optimized import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 连接设备

```python
import requests

# 连接设备
response = requests.post("http://localhost:8000/device/connect", json={
    "serial_id": "123.56.152.41:6529"
})
print(response.json())
```

### 查找元素

```python
# 查找元素
response = requests.post("http://localhost:8000/element/find", json={
    "serial_id": "123.56.152.41:6529",
    "method": "css selector",
    "selector": ".my-class"
})
print(response.json())
```

## 优势

1. **模块化设计**: 按功能分离，便于维护和扩展
2. **清晰的API结构**: 使用前缀路由，API路径更加清晰
3. **统一的错误处理**: 所有接口使用统一的响应格式
4. **完整的文档**: 自动生成API文档
5. **易于测试**: 每个模块可以独立测试

## 迁移指南

从原来的 `server.py` 迁移到新的模块化结构：

1. 更新导入路径
2. 使用新的API端点（添加前缀）
3. 更新客户端代码中的URL

### 旧API到新API的映射

| 旧API | 新API |
|-------|-------|
| `POST /connect` | `POST /device/connect` |
| `POST /disconnect` | `POST /device/disconnect` |
| `POST /find_element` | `POST /element/find` |
| `POST /find_elements` | `POST /element/find_all` |
| `POST /click` | `POST /element/click` |
| `POST /run_operations` | `POST /element/operations` |
| `POST /check_page` | `POST /page/check` |
| `POST /collect_items` | `POST /collect/items` |
| `POST /mock_click` | `POST /mock/click` |
| `POST /mock_find_element` | `POST /mock/find_element` | 