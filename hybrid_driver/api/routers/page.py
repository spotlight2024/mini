import logging
from fastapi import APIRouter

from hybrid_driver.device_pool import DevicePool
from hybrid_driver.utils.async_utils import run_sync
from hybrid_driver.api.utils import check_page_type, detect_current_page
from hybrid_driver.log_config import get_logger

router = APIRouter(prefix="/page", tags=["页面管理"])
logger = get_logger(__name__)


@router.post("/check")
async def check_page(request: dict):
    """检查当前页面状态"""
    try:
        serial_id = request.get("serial_id")
        required_page = request.get("required_page")
        
        if not serial_id:
            return {"code": 1, "message": "serial_id is required"}
        
        if not required_page:
            return {"code": 1, "message": "required_page is required"}
        
        # 获取设备
        device = await run_sync(DevicePool().get, serial_id)
        if device is None:
            return {"code": 2, "message": f"Device {serial_id} not found"}
        
        try:
            # 获取当前页面信息
            current_url = await run_sync(device.get_current_url)
            page_source = await run_sync(device.get_page_source)
            
            # 确保返回的是字符串类型
            current_url_str = str(current_url) if current_url is not None else ""
            page_source_str = str(page_source) if page_source is not None else ""
            
            # 简单的页面检测逻辑，可以根据需要扩展
            is_current_page = check_page_type(current_url_str, page_source_str, required_page)
            
            return {
                "code": 0,
                "message": "Page check completed",
                "isCurrentPage": is_current_page,
                "currentPage": detect_current_page(current_url_str, page_source_str),
                "currentUrl": current_url_str
            }
            
        except Exception as e:
            logging.error(f"Page check failed: {str(e)}")
            return {
                "code": 3,
                "message": f"Page check error: {str(e)}"
            }
    
    except Exception as e:
        logging.error(f"Check page request failed: {str(e)}")
        return {
            "code": 4,
            "message": f"Request processing error: {str(e)}"
        } 