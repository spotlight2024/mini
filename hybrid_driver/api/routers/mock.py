import time
import asyncio
import random
import logging
from fastapi import APIRouter

from hybrid_driver.api.models import ClickRequest, FindElementRequest, APIResponse
from hybrid_driver.log_config import get_logger

router = APIRouter(prefix="/mock", tags=["模拟测试"])
logger = get_logger(__name__)


@router.post("/click", response_model=APIResponse)
async def mock_click(req: ClickRequest):
    """模拟点击操作"""
    delay = random.uniform(5, 30)
    start = time.time()
    logging.info(f"收到 mock_click 请求: {req.dict()}，模拟耗时 {delay:.2f} 秒")
    await asyncio.sleep(delay)
    end = time.time()
    process_time = end - start
    logging.info(f"mock_click 处理完成，delay={delay:.2f}，process_time={process_time:.2f}")
    return APIResponse(
        code=0,
        message=f"模拟点击成功，耗时{delay:.2f}秒",
        data={
            "method": req.method,
            "selector": req.selector,
            "mock_delay": delay,
            "process_time": process_time
        }
    )


@router.post("/find_element", response_model=APIResponse)
async def mock_find_element(req: FindElementRequest):
    """模拟查找元素操作"""
    delay = random.uniform(5, 30)
    start = time.time()
    logging.info(f"收到 mock_find_element 请求: {req.dict()}，模拟耗时 {delay:.2f} 秒")
    await asyncio.sleep(delay)
    end = time.time()
    process_time = end - start
    logging.info(f"mock_find_element 处理完成，delay={delay:.2f}，process_time={process_time:.2f}")
    return APIResponse(
        code=0,
        message=f"模拟查找元素成功，耗时{delay:.2f}秒",
        data={
            "element": f"mock_element_{req.selector}",
            "mock_delay": delay,
            "process_time": process_time
        }
    ) 