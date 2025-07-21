from fastapi import APIRouter
from datetime import datetime
from typing import TypeVar, Callable, cast

from fastapi import APIRouter

from hybrid_driver.api.models import (
    ConnectRequest, ConnectConfig, DisconnectRequest, ActionRequest, APIResponse,
    ConnectionData, ErrorData, DeviceInfo, DeviceCapabilities
)
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.log_config import get_logger
from hybrid_driver.utils.async_utils import run_sync
from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor

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
            session_id = "unknown"
            
            if web_executor and hasattr(web_executor, 'get_raw_remote_webdriver'):
                try:
                    raw_driver = web_executor.get_raw_remote_webdriver()
                    if raw_driver:
                        # 获取session_id但不关闭driver
                        session_id = str(raw_driver.session_id) if raw_driver else "unknown"
                        logger.info(f"获取到session_id: {session_id}")
                    else:
                        logger.warning("raw_driver为None")
                except Exception as e:
                    logger.error(f"获取session_id失败: {e}")
                    session_id = "unknown"
            else:
                logger.warning("web_executor未初始化或没有get_raw_remote_webdriver方法")
            
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
            
            # 获取可见页面并切换
            web_executor = device.web_executor
            if web_executor is None:
                logger.error("WebExecutor未初始化")
                return APIResponse(
                    code=1004, 
                    message="WebExecutor未初始化",
                    data=connection_data.model_dump()
                )
            
            # 类型检查
            if not isinstance(web_executor, SeleniumWebExecutor):
                logger.error(f"WebExecutor类型错误: {type(web_executor)}")
                return APIResponse(
                    code=1004, 
                    message="WebExecutor类型错误",
                    data=connection_data.model_dump()
                )
            
            executor: SeleniumWebExecutor = web_executor
            driver = executor.get_raw_remote_webdriver()
            if driver is None:
                logger.error("WebExecutor未初始化")
                return APIResponse(
                    code=1004, 
                    message="WebExecutor未初始化",
                    data=connection_data.model_dump()
                )

            pages = await run_sync_typed(executor.get_visible_pages)

            logger.info(f"pages : ${pages}")
            try:
                data_dict = connection_data.model_dump()
            except AttributeError as e:
                logger.error(f"connection_data 没有 model_dump 方法: {e}")
                data_dict = {
                    "session_id": session_id,
                    "serial_id": req.serial_id,
                    "user_id": req.user_id,
                    "status": "connected"
                }
            
            return APIResponse(
                code=0, 
                message="设备连接成功", 
                data=data_dict
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
            
            try:
                error_dict = error_data.model_dump()
            except AttributeError as e:
                logger.error(f"error_data 没有 model_dump 方法: {e}")
                error_dict = {
                    "serial_id": req.serial_id,
                    "error_reason": "设备不可用或连接超时"
                }
            
            return APIResponse(
                code=1001, 
                message="设备连接失败",
                data=error_dict
            )
    except Exception as ex:
        logger.error(f"连接设备异常: {ex}")
        return APIResponse(
            code=2000, 
            message="连接设备时发生异常", 
            error=str(ex),
            data={
                "serial_id": req.serial_id,
                "exception_type": type(ex).__name__
            }
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