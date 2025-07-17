# JSON 响应格式优化指南

## 概述

本文档介绍如何在 `hybrid_driver` API 中优雅地返回 JSON 格式的数据，提供类型安全、结构化的响应格式。

## 优化方案对比

### 1. 原始方式（不推荐）
```python
# ❌ 原始方式：直接返回字典
return APIResponse(
    code=0, 
    message="success",
    data={
        "session_id": session_id,
        "serial_id": req.serial_id,
        "user_id": req.user_id,
        "status": "connected"
    }
)
```

**问题**：
- 类型不安全
- 结构不统一
- 难以维护
- 缺乏文档

### 2. Pydantic 模型方式（推荐）
```python
# ✅ 优雅方式：使用 Pydantic 模型
connection_data = ConnectionData(
    session_id=session_id,
    serial_id=req.serial_id,
    user_id=req.user_id,
    status="connected",
    device_info=DeviceInfo(
        platform="android",
        webdriver_type="selenium",
        connection_time=datetime.now()
    ),
    capabilities=DeviceCapabilities(
        browser_name="chrome",
        platform_name="android"
    )
)

return APIResponse(
    code=0, 
    message="设备连接成功", 
    data=connection_data.model_dump()
)
```

**优势**：
- 类型安全
- 自动验证
- 结构统一
- 自动生成文档
- 易于维护

## 响应模型设计

### 1. 基础响应模型
```python
class APIResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None
```

### 2. 业务数据模型
```python
class ConnectionData(BaseModel):
    session_id: str = Field(description="WebDriver会话ID")
    serial_id: str = Field(description="设备序列号")
    user_id: str = Field(description="用户ID")
    status: str = Field(default="connected", description="连接状态")
    device_info: DeviceInfo = Field(description="设备信息")
    capabilities: DeviceCapabilities = Field(description="设备能力")
```

### 3. 错误数据模型
```python
class ErrorData(BaseModel):
    serial_id: str = Field(description="设备序列号")
    error_reason: str = Field(description="错误原因")
    suggestions: List[str] = Field(default=[], description="解决建议")
    exception_type: Optional[str] = Field(default=None, description="异常类型")
    error_details: Optional[str] = Field(default=None, description="详细错误信息")
```

## 使用示例

### 1. 连接成功响应
```python
@router.post("/connect", response_model=APIResponse)
async def connect(req: ConnectRequest):
    try:
        device = await run_sync_typed(DevicePool().connect, req.serial_id)
        if device is not None:
            # 获取会话ID
            web_executor = device.get_web_driver()
            session_id = "unknown"
            if web_executor and hasattr(web_executor, 'get_raw_remote_webdriver'):
                try:
                    raw_driver = web_executor.get_raw_remote_webdriver()
                    session_id = str(raw_driver.session_id) if raw_driver else "unknown"
                except Exception:
                    session_id = "unknown"
            
            # 构建响应数据
            connection_data = ConnectionData(
                session_id=session_id,
                serial_id=req.serial_id,
                user_id=req.user_id,
                status="connected",
                device_info=DeviceInfo(
                    platform="android",
                    webdriver_type="selenium",
                    connection_time=datetime.now()
                ),
                capabilities=DeviceCapabilities(
                    browser_name="chrome",
                    platform_name="android"
                )
            )
            
            return APIResponse(
                code=0, 
                message="设备连接成功", 
                data=connection_data.model_dump()
            )
```

### 2. 错误响应
```python
        else:
            error_data = ErrorData(
                serial_id=req.serial_id,
                error_reason="设备不可用或连接超时",
                suggestions=[
                    "检查设备是否已连接",
                    "确认设备序列号是否正确",
                    "检查网络连接状态"
                ]
            )
            
            return APIResponse(
                code=1001, 
                message="设备连接失败",
                data=error_data.model_dump()
            )
```

### 3. 异常响应
```python
    except Exception as ex:
        logger.error(f"连接设备异常: {ex}")
        error_data = ErrorData(
            serial_id=req.serial_id,
            error_reason="系统异常",
            exception_type=type(ex).__name__,
            error_details=str(ex)
        )
        
        return APIResponse(
            code=2000, 
            message="系统异常", 
            error=str(ex),
            data=error_data.model_dump()
        )
```

## 响应格式示例

### 1. 连接成功
```json
{
  "code": 0,
  "message": "设备连接成功",
  "data": {
    "session_id": "abc123def456",
    "serial_id": "172.16.1.125:6524",
    "user_id": "user123",
    "status": "connected",
    "device_info": {
      "platform": "android",
      "webdriver_type": "selenium",
      "connection_time": "2024-01-15T10:30:00"
    },
    "capabilities": {
      "browser_name": "chrome",
      "platform_name": "android",
      "browser_version": null
    }
  },
  "error": null,
  "trace_id": null
}
```

### 2. 连接失败
```json
{
  "code": 1001,
  "message": "设备连接失败",
  "data": {
    "serial_id": "172.16.1.125:6524",
    "error_reason": "设备不可用或连接超时",
    "suggestions": [
      "检查设备是否已连接",
      "确认设备序列号是否正确",
      "检查网络连接状态"
    ],
    "exception_type": null,
    "error_details": null
  },
  "error": null,
  "trace_id": null
}
```

### 3. 系统异常
```json
{
  "code": 2000,
  "message": "系统异常",
  "data": {
    "serial_id": "172.16.1.125:6524",
    "error_reason": "系统异常",
    "suggestions": [],
    "exception_type": "ConnectionError",
    "error_details": "Failed to connect to device"
  },
  "error": "Failed to connect to device",
  "trace_id": null
}
```

## 最佳实践

### 1. 模型设计原则
- **单一职责**：每个模型只负责一种数据类型
- **字段验证**：使用 Field 添加验证和描述
- **默认值**：为可选字段提供合理的默认值
- **文档化**：使用 description 字段提供文档

### 2. 错误处理
- **统一格式**：所有错误使用相同的 ErrorData 模型
- **详细信息**：提供错误原因和解决建议
- **异常类型**：记录具体的异常类型
- **日志记录**：在返回错误前记录日志

### 3. 性能优化
- **延迟计算**：只在需要时计算复杂字段
- **缓存结果**：对重复计算的结果进行缓存
- **异步处理**：使用异步操作提高响应速度

### 4. 扩展性
- **版本兼容**：新版本保持向后兼容
- **字段扩展**：预留扩展字段
- **模型继承**：使用继承减少重复代码

## 工具函数

### 1. 响应构建器
```python
def build_success_response(data: BaseModel, message: str = "操作成功") -> APIResponse:
    """构建成功响应"""
    return APIResponse(
        code=0,
        message=message,
        data=data.model_dump()
    )

def build_error_response(
    serial_id: str, 
    error_reason: str, 
    suggestions: List[str] = None,
    exception: Exception = None
) -> APIResponse:
    """构建错误响应"""
    error_data = ErrorData(
        serial_id=serial_id,
        error_reason=error_reason,
        suggestions=suggestions or [],
        exception_type=type(exception).__name__ if exception else None,
        error_details=str(exception) if exception else None
    )
    
    return APIResponse(
        code=1001,
        message="操作失败",
        data=error_data.model_dump(),
        error=str(exception) if exception else None
    )
```

### 2. 使用示例
```python
# 成功响应
return build_success_response(connection_data, "设备连接成功")

# 错误响应
return build_error_response(
    serial_id=req.serial_id,
    error_reason="设备不可用",
    suggestions=["检查设备连接"],
    exception=ex
)
```

## 总结

使用 Pydantic 模型的方式提供了：
1. **类型安全**：编译时检查类型错误
2. **自动验证**：自动验证数据格式
3. **文档生成**：自动生成 API 文档
4. **维护性**：统一的代码结构和错误处理
5. **扩展性**：易于添加新字段和功能

这种方式比直接返回字典更加优雅、安全和可维护。 