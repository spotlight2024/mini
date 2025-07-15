import logging
from fastapi import APIRouter

from hybrid_driver.api.models import ConnectRequest, DisconnectRequest, ActionRequest, APIResponse
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.utils.async_utils import run_sync
from hybrid_driver.log_config import get_logger

router = APIRouter(prefix="/device", tags=["设备管理"])
logger = get_logger(__name__)


@router.post("/connect", response_model=APIResponse)
async def connect(req: ConnectRequest):
    """连接设备"""
    try:
        device = await run_sync(DevicePool().connect, req.serial_id)
        if device is not None:
            return APIResponse(code=0, message="success")
        else:
            return APIResponse(code=1001, message="连接失败")
    except Exception as ex:
        return APIResponse(code=2000, message="系统异常", error=str(ex))


@router.post("/disconnect", response_model=APIResponse)
async def disconnect(req: DisconnectRequest):
    """断开设备连接"""
    device = await run_sync(DevicePool().get, req.serial_id)
    if device is None:
        return APIResponse(code=1002, message="device not found")
    else:
        await run_sync(device.disconnect)
        return APIResponse(code=0, message="success")


@router.post("/action", response_model=APIResponse)
async def action(req: ActionRequest):
    """执行设备操作"""
    device = await run_sync(DevicePool().get, req.serial_id)
    if device is None:
        return APIResponse(code=1002, message="device not found")
    # TODO: 实现具体的action逻辑
    return APIResponse(code=0, message="success") 