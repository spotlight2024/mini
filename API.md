# SpotLight Script服务 API 文档

## 概述

本文档详细描述了SpotLight Script服务的所有API接口，包括请求格式、响应格式、错误码和示例。

## 基础信息

### 服务地址
- **开发环境**: `http://localhost:8000`
- **生产环境**: `https://your-domain.com`

### 请求格式
- **Content-Type**: `application/json`
- **字符编码**: UTF-8

### 响应格式
所有API响应都遵循统一的格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "error": null,
  "trace_id": "uuid-string"
}
```

### 响应码说明
| 响应码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 连接失败 |
| 1002 | 设备未找到 |
| 1003 | 元素未找到 |
| 2000 | 系统异常 |
| 400101 | 设备未找到（带trace_id） |

## 设备管理接口

### 1. 连接设备

**接口地址**: `POST /connect`

**功能描述**: 连接到指定的Android设备

**请求参数**:
```json
{
  "serial_id": "string",
  "ip": "string (可选)",
  "port": "number (可选)"
}
```

**参数说明**:
- `serial_id`: 设备序列号，必填
- `ip`: 设备IP地址，可选
- `port`: 设备端口，可选

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": null,
  "error": null,
  "trace_id": null
}
```

**错误响应**:
```json
{
  "code": 1001,
  "message": "连接失败",
  "data": null,
  "error": "Connection timeout",
  "trace_id": null
}
```

**使用示例**:
```bash
curl -X POST http://localhost:8000/connect \
  -H "Content-Type: application/json" \
  -d '{
    "serial_id": "JJGICIN7QOAELNGI",
    "ip": "172.16.1.125",
    "port": 6520
  }'
```

### 2. 断开设备

**接口地址**: `POST /disconnect`

**功能描述**: 断开指定设备的连接

**请求参数**:
```json
{
  "serial_id": "string"
}
```

**参数说明**:
- `serial_id`: 设备序列号，必填

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": null,
  "error": null,
  "trace_id": null
}
```

**使用示例**:
```bash
curl -X POST http://localhost:8000/disconnect \
  -H "Content-Type: application/json" \
  -d '{
    "serial_id": "JJGICIN7QOAELNGI"
  }'
```

### 3. 健康检查

**接口地址**: `GET /health`

**功能描述**: 检查服务健康状态

**请求参数**: 无

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "device_count": 2,
    "version": "1.0.0"
  },
  "error": null,
  "trace_id": null
}
```

**使用示例**:
```bash
curl -X GET http://localhost:8000/health
```

## 元素操作接口

### 1. 查找元素

**接口地址**: `POST /find_element`

**功能描述**: 在指定设备上查找元素

**请求参数**:
```json
{
  "serial_id": "string",
  "method": "string",
  "selector": "string",
  "timeout": "number (可选)"
}
```

**参数说明**:
- `serial_id`: 设备序列号，必填
- `method`: 定位方法，必填，支持以下值：
  - `"id"` - 通过ID定位
  - `"xpath"` - 通过XPath定位
  - `"css selector"` - 通过CSS选择器定位
  - `"name"` - 通过name属性定位
  - `"class name"` - 通过class名称定位
  - `"tag name"` - 通过标签名定位
  - `"link text"` - 通过链接文本定位
  - `"partial link text"` - 通过部分链接文本定位
- `selector`: 定位表达式，必填
- `timeout`: 超时时间（秒），可选，默认3秒

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "element": "<WebElement>",
    "tag_name": "div",
    "text": "按钮文本",
    "attributes": {
      "id": "button-id",
      "class": "button-class"
    }
  },
  "error": null,
  "trace_id": null
}
```

**错误响应**:
```json
{
  "code": 1003,
  "message": "element not found",
  "data": null,
  "error": "Element not found with selector: #button",
  "trace_id": null
}
```

**使用示例**:
```bash
curl -X POST http://localhost:8000/find_element \
  -H "Content-Type: application/json" \
  -d '{
    "serial_id": "JJGICIN7QOAELNGI",
    "method": "css selector",
    "selector": ".wx-scroll-view",
    "timeout": 5
  }'
```

### 2. 执行单个操作

**接口地址**: `POST /action`

**功能描述**: 在指定设备上执行单个操作

**请求参数**:
```json
{
  "serial_id": "string",
  "type": "string",
  "params": {}
}
```

**参数说明**:
- `serial_id`: 设备序列号，必填
- `type`: 操作类型，必填
- `params`: 操作参数，可选

**支持的操作类型**:
- `click`: 点击操作
- `input`: 文本输入
- `wait`: 等待操作
- `js`: JavaScript执行

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "result": true,
    "duration": 0.5
  },
  "error": null,
  "trace_id": null
}
```

**使用示例**:
```bash
# 点击操作
curl -X POST http://localhost:8000/action \
  -H "Content-Type: application/json" \
  -d '{
    "serial_id": "JJGICIN7QOAELNGI",
    "type": "click",
    "params": {
      "selector": "#button"
    }
  }'

# 文本输入
curl -X POST http://localhost:8000/action \
  -H "Content-Type: application/json" \
  -d '{
    "serial_id": "JJGICIN7QOAELNGI",
    "type": "input",
    "params": {
      "selector": "#input",
      "text": "输入文本"
    }
  }'
```

## 操作序列接口

### 1. 执行操作序列

**接口地址**: `POST /run_operations`

**功能描述**: 在指定设备上执行一系列操作

**请求参数**:
```json
{
  "serial_id": "string",
  "operations": [
    {
      "type": "string",
      "method": "string (可选)",
      "selector": "string (可选)",
      "timeout": "number (可选)",
      "seconds": "number (可选)",
      "script": "string (可选)",
      "popup_selector": "string (可选)",
      "wait_for_new_window": "boolean (可选)",
      "wait_for_render": "boolean (可选)"
    }
  ]
}
```

**参数说明**:
- `serial_id`: 设备序列号，必填
- `operations`: 操作列表，必填

**操作类型详细说明**:

#### 基础操作
- `find`: 查找元素
  ```json
  {
    "type": "find",
    "method": "css selector",
    "selector": ".element",
    "timeout": 10
  }
  ```

- `click`: 点击操作
  ```json
  {
    "type": "click",
    "method": "css selector",
    "selector": "#button",
    "wait_for_new_window": true,
    "timeout": 10
  }
  ```

- `input`: 文本输入
  ```json
  {
    "type": "input",
    "text": "输入文本",
    "timeout": 10
  }
  ```

- `wait`: 等待操作
  ```json
  {
    "type": "wait",
    "seconds": 5
  }
  ```

#### 高级操作
- `wait_for_new_window`: 等待新窗口
  ```json
  {
    "type": "wait_for_new_window",
    "timeout": 10
  }
  ```

- `wait_for_page_render`: 等待页面渲染
  ```json
  {
    "type": "wait_for_page_render",
    "timeout": 10
  }
  ```

- `js`: JavaScript执行
  ```json
  {
    "type": "js",
    "script": "document.getElementById('element').click();"
  }
  ```

- `handle_popup`: 处理弹窗
  ```json
  {
    "type": "handle_popup",
    "popup_selector": ".popup-close",
    "timeout": 3
  }
  ```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "results": [
      {
        "step": 1,
        "action": "FindElement",
        "success": true,
        "result": "Element found",
        "error": null,
        "elapsed": 0.1
      },
      {
        "step": 2,
        "action": "Click",
        "success": true,
        "result": "Clicked successfully",
        "error": null,
        "elapsed": 0.2
      }
    ],
    "total_steps": 2,
    "success_count": 2,
    "failure_count": 0,
    "total_elapsed": 0.3
  },
  "error": null,
  "trace_id": "uuid-string"
}
```

**使用示例**:
```bash
curl -X POST http://localhost:8000/run_operations \
  -H "Content-Type: application/json" \
  -d '{
    "serial_id": "JJGICIN7QOAELNGI",
    "operations": [
      {
        "type": "find",
        "method": "css selector",
        "selector": "#search-input",
        "timeout": 10
      },
      {
        "type": "input",
        "text": "搜索内容"
      },
      {
        "type": "click",
        "method": "css selector",
        "selector": "#search-button"
      }
    ]
  }'
```

## 状态查询接口

### 1. 获取设备状态

**接口地址**: `POST /status`

**功能描述**: 获取指定设备的状态信息

**请求参数**:
```json
{
  "serial_id": "string"
}
```

**参数说明**:
- `serial_id`: 设备序列号，必填

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "serial_id": "JJGICIN7QOAELNGI",
    "status": "connected",
    "connected_at": "2024-01-01T12:00:00Z",
    "last_active": "2024-01-01T12:05:00Z",
    "current_url": "https://example.com",
    "page_title": "页面标题",
    "window_handles": ["handle1", "handle2"]
  },
  "error": null,
  "trace_id": null
}
```

**使用示例**:
```bash
curl -X POST http://localhost:8000/status \
  -H "Content-Type: application/json" \
  -d '{
    "serial_id": "JJGICIN7QOAELNGI"
  }'
```

### 2. 获取所有设备状态

**接口地址**: `GET /devices`

**功能描述**: 获取所有连接设备的状态信息

**请求参数**: 无

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "devices": [
      {
        "serial_id": "JJGICIN7QOAELNGI",
        "status": "connected",
        "connected_at": "2024-01-01T12:00:00Z",
        "last_active": "2024-01-01T12:05:00Z"
      },
      {
        "serial_id": "DEVICE2",
        "status": "disconnected",
        "connected_at": null,
        "last_active": null
      }
    ],
    "total_count": 2,
    "connected_count": 1,
    "disconnected_count": 1
  },
  "error": null,
  "trace_id": null
}
```

**使用示例**:
```bash
curl -X GET http://localhost:8000/devices
```

## 错误处理

### 1. 错误码说明

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 1001 | 连接失败 | 检查设备是否可用，网络是否连通 |
| 1002 | 设备未找到 | 确认设备序列号正确，设备已连接 |
| 1003 | 元素未找到 | 检查元素选择器是否正确，页面是否加载完成 |
| 2000 | 系统异常 | 查看服务日志，联系技术支持 |
| 400101 | 设备未找到（带trace_id） | 确认设备序列号正确，设备已连接 |

### 2. 常见错误响应

#### 设备连接失败
```json
{
  "code": 1001,
  "message": "连接失败",
  "data": null,
  "error": "Connection timeout after 30 seconds",
  "trace_id": null
}
```

#### 元素未找到
```json
{
  "code": 1003,
  "message": "element not found",
  "data": null,
  "error": "Element not found with selector: #non-existent-element",
  "trace_id": null
}
```

#### 系统异常
```json
{
  "code": 2000,
  "message": "系统异常",
  "data": null,
  "error": "WebDriver initialization failed",
  "trace_id": "uuid-string"
}
```

## 最佳实践

### 1. 错误处理
```python
import requests

def call_api(endpoint, data):
    try:
        response = requests.post(f"http://localhost:8000/{endpoint}", json=data)
        result = response.json()
        
        if result["code"] == 0:
            return result["data"]
        else:
            print(f"API调用失败: {result['message']}")
            print(f"错误详情: {result['error']}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        return None
```

### 2. 操作序列示例
```python
# 完整的操作序列示例
operations = [
    # 1. 等待页面加载
    {"type": "wait_for_page_render", "timeout": 10},
    
    # 2. 查找搜索框
    {"type": "find", "method": "css selector", "selector": "#search-input", "timeout": 10},
    
    # 3. 输入搜索内容
    {"type": "input", "text": "搜索关键词"},
    
    # 4. 点击搜索按钮
    {"type": "click", "method": "css selector", "selector": "#search-button"},
    
    # 5. 等待新页面加载
    {"type": "wait_for_new_window", "timeout": 10},
    
    # 6. 处理可能的弹窗
    {"type": "handle_popup", "popup_selector": ".popup-close", "timeout": 3}
]

# 执行操作序列
response = requests.post("http://localhost:8000/run_operations", json={
    "serial_id": "DEVICE_ID",
    "operations": operations
})
```

### 3. 性能优化
- 使用操作序列而不是单个操作，减少网络开销
- 合理设置超时时间，避免长时间等待
- 及时断开不需要的设备连接
- 使用适当的元素定位方法（ID > CSS > XPath）

## 版本信息

- **当前版本**: v1.0.0
- **API版本**: v1
- **最后更新**: 2024-01-01

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持基础设备管理接口
- 支持元素查找和操作接口
- 支持操作序列执行接口
- 支持状态查询接口 