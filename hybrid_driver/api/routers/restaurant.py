"""
餐厅管理API路由
"""
import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from hybrid_driver.api.models import APIResponse
from hybrid_driver.business_framework.business.restaurant_business import RestaurantBusiness
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.utils.async_utils import run_sync
from hybrid_driver.log_config import get_logger

router = APIRouter(prefix="/restaurant", tags=["餐厅管理"])
logger = get_logger(__name__)


class RestaurantInfo(BaseModel):
    """餐厅信息模型"""
    name: str = Field(description="餐厅名称")
    shop_id: str = Field(description="店铺ID")
    queue_status: str = Field(description="排队状态")
    waiting_tables: str = Field(default="", description="等待桌数")
    rating_info: str = Field(default="", description="评分信息")
    address: str = Field(default="", description="地址信息")


class RestaurantListResponse(BaseModel):
    """餐厅列表响应模型"""
    total_count: int = Field(description="餐厅总数")
    restaurants: List[RestaurantInfo] = Field(description="餐厅列表")


class ExtractRestaurantsRequest(BaseModel):
    """提取餐厅信息请求模型"""
    serial_id: str = Field(description="设备序列号")


@router.post("/extract", response_model=APIResponse, summary="提取当前页面餐厅信息")
async def extract_restaurants(req: ExtractRestaurantsRequest):
    """提取当前页面的餐厅信息"""
    try:
        # 获取设备
        device = await run_sync(DevicePool().get, req.serial_id)
        if device is None:
            return APIResponse(
                code=1002,
                message="设备未找到",
                error=f"Device {req.serial_id} not found"
            )
        
        # 创建餐厅业务实例（不需要初始化，直接使用现有的driver）
        restaurant_business = RestaurantBusiness(req.serial_id)
        
        # 使用设备的driver
        web_executor = device.get_web_driver()
        if not web_executor or not hasattr(web_executor, 'get_raw_remote_webdriver'):
            return APIResponse(
                code=1004,
                message="WebDriver未初始化",
                error="WebDriver not initialized"
            )
        
        driver = web_executor.get_raw_remote_webdriver()
        if not driver:
            return APIResponse(
                code=1004,
                message="WebDriver未初始化",
                error="WebDriver not initialized"
            )
        
        # 直接使用现有的driver提取餐厅信息
        restaurants_data = restaurant_business.extract_restaurant_info_js(driver)
        
        if restaurants_data:
            # 转换为响应模型
            restaurants = [
                RestaurantInfo(
                    name=r.get('name', ''),
                    shop_id=r.get('shop_id', ''),
                    queue_status=r.get('queue_status', ''),
                    waiting_tables=r.get('waiting_tables', ''),
                    rating_info=r.get('rating_info', ''),
                    address=r.get('address', '')
                )
                for r in restaurants_data
            ]
            
            response_data = RestaurantListResponse(
                total_count=len(restaurants),
                restaurants=restaurants
            )
            
            return APIResponse(
                code=0,
                message="餐厅信息提取成功",
                data=response_data.model_dump()
            )
        else:
            return APIResponse(
                code=1003,
                message="未找到餐厅信息",
                error="No restaurants found on current page"
            )
            
    except Exception as e:
        logger.error(f"提取餐厅信息失败: {e}")
        return APIResponse(
            code=2000,
            message="系统异常",
            error=str(e)
        )


@router.get("/health", summary="健康检查")
def health_check():
    """餐厅API健康检查"""
    return {
        "status": "healthy",
        "service": "餐厅管理 API",
        "version": "1.0.0"
    }
