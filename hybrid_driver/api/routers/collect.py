import logging
from fastapi import APIRouter

from hybrid_driver.api.models import CollectItemsRequest, APIResponse
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.operation import CollectItemsOp
from hybrid_driver.utils.async_utils import run_sync
from hybrid_driver.api.utils import gen_trace_id
from hybrid_driver.log_config import get_logger

router = APIRouter(prefix="/collect", tags=["数据收集"])
logger = get_logger(__name__)


@router.post("/items", response_model=APIResponse)
async def collect_items(req: CollectItemsRequest):
    """
    收集元素信息接口 - Web端ACTION_COLLECT_ITEM_INFO实现
    支持新协议JSON配置和老协议参数
    """
    trace_id = gen_trace_id()
    try:
        device = await run_sync(DevicePool().get, req.serial_id)
        if device is None:
            return APIResponse(
                code=1002, 
                message="设备未找到", 
                error=f"Device {req.serial_id} not found",
                trace_id=trace_id
            )
        
        # 创建收集操作，支持新协议和老协议
        if req.config_json or req.config_file:
            collect_op = CollectItemsOp(
                config_json=req.config_json,
                config_file=req.config_file
            )
        else:
            collect_op = CollectItemsOp(
                container_selector=req.container_selector,
                item_selectors=req.item_selectors or {},
                options=req.options or {},
                filters=req.filters or {},
                dialog_views=req.dialog_views or [],
                loading_view=req.loading_view,
                close_dialog=req.close_dialog if req.close_dialog is not None else True,
                package_name=req.package_name
            )
        
        # 执行收集操作
        result = await run_sync(collect_op.execute, device)
        
        if result:
            return APIResponse(
                code=0, 
                message="收集成功", 
                data=result,
                trace_id=trace_id
            )
        else:
            return APIResponse(
                code=1003, 
                message="收集失败", 
                error="No items collected",
                trace_id=trace_id
            )
            
    except Exception as e:
        return APIResponse(
            code=2000, 
            message="系统异常", 
            error=str(e),
            trace_id=trace_id
        ) 