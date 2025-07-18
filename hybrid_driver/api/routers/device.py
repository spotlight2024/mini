import logging
from fastapi import APIRouter
from requests import session
from typing import Dict, Any, Optional
from datetime import datetime

from hybrid_driver.api.models import (
    ConnectRequest, ConnectConfig, DisconnectRequest, ActionRequest, APIResponse,
    ConnectionData, ErrorData, DisconnectData, ActionData,
    DeviceInfo, DeviceCapabilities
)
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.utils.async_utils import run_sync
from hybrid_driver.log_config import get_logger
from hybrid_driver.device.android_device import AndroidDevice
from typing import TypeVar, Callable, Awaitable, cast

router = APIRouter(prefix="/device", tags=["设备管理"])
logger = get_logger(__name__)

T = TypeVar('T')
async def run_sync_typed(func: Callable[..., T], *args, **kwargs) -> T:
    from hybrid_driver.utils.async_utils import run_sync
    result = await run_sync(func, *args, **kwargs)
    return cast(T, result)


@router.post("/connect", response_model=APIResponse)
async def connect(req: ConnectRequest):
    """连接设备"""
    try:
        # 将 ConnectRequest 转换为 ConnectConfig
        config = ConnectConfig(
            serial_id=req.serial_id,
            user_id=req.user_id,
            android_process=req.android_process
        )
        device = await run_sync_typed(DevicePool().connect, config)  # 类型安全
        if device is not None:
            web_executor = device.get_web_driver()
            if web_executor and hasattr(web_executor, 'get_raw_remote_webdriver'):
                try:
                    raw_driver = web_executor.get_raw_remote_webdriver()
                    session_id = str(raw_driver.session_id) if raw_driver else "unknown"
                except Exception:
                    session_id = "unknown"
            else:
                session_id = "unknown"
            
            # 使用 Pydantic 模型构建响应数据
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


@router.post("/disconnect", response_model=APIResponse)
async def disconnect(req: DisconnectRequest):
    """断开设备连接"""
    try:
        device = await run_sync(DevicePool().get, req.serial_id)
        if device is None:
            return APIResponse(
                code=1002, 
                message="设备未找到",
                data={
                    "serial_id": req.serial_id,
                    "status": "not_found"
                }
            )
        else:
            await run_sync(device.disconnect)
            return APIResponse(
                code=0, 
                message="设备断开连接成功",
                data={
                    "serial_id": req.serial_id,
                    "status": "disconnected",
                    "disconnect_time": None  # 可以添加断开时间戳
                }
            )
    except Exception as ex:
        logger.error(f"断开设备连接异常: {ex}")
        return APIResponse(
            code=2000, 
            message="断开连接时发生异常", 
            error=str(ex),
            data={
                "serial_id": req.serial_id,
                "exception_type": type(ex).__name__
            }
        )


@router.post("/action", response_model=APIResponse)
async def action(req: ActionRequest):
    """执行设备操作"""
    try:
        device = await run_sync(DevicePool().get, req.serial_id)
        if device is None:
            return APIResponse(
                code=1002, 
                message="设备未找到",
                data={
                    "serial_id": req.serial_id,
                    "action_type": req.type,
                    "status": "device_not_found"
                }
            )
        
        # TODO: 实现具体的action逻辑
        action_result = {
            "serial_id": req.serial_id,
            "action_type": req.type,
            "params": req.params,
            "status": "executed",
            "result": "success",
            "execution_time": None  # 可以添加执行时间戳
        }
        
        return APIResponse(
            code=0, 
            message="操作执行成功",
            data=action_result
        )
    except Exception as ex:
        logger.error(f"执行设备操作异常: {ex}")
        return APIResponse(
            code=2000, 
            message="操作执行异常", 
            error=str(ex),
            data={
                "serial_id": req.serial_id,
                "action_type": req.type,
                "exception_type": type(ex).__name__,
                "error_details": str(ex)
            }
        ) 