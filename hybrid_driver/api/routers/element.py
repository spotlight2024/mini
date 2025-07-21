import logging
from fastapi import APIRouter

from hybrid_driver.api.models import (
    FindElementRequest, ClickRequest, APIResponse,
    OperationRequest, OperationItem, RunScript
)
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.operation import OperationSequence, build_operations
from hybrid_driver.utils.async_utils import run_sync
from hybrid_driver.api.utils import gen_trace_id
from hybrid_driver.log_config import get_logger

router = APIRouter(prefix="/element", tags=["元素操作"])
logger = get_logger(__name__)


@router.post("/find", response_model=APIResponse)
async def find_element(req: FindElementRequest):
    """
    查找元素接口。
    参数 method 必须为以下字符串之一（与 Selenium By 枚举一一对应）：
        "id"               -> By.ID
        "xpath"            -> By.XPATH
        "css selector"     -> By.CSS_SELECTOR
        "name"             -> By.NAME
        "class name"       -> By.CLASS_NAME
        "tag name"         -> By.TAG_NAME
        "link text"        -> By.LINK_TEXT
        "partial link text"-> By.PARTIAL_LINK_TEXT
    selector 为具体的定位表达式。
    例如：
        method="css selector", selector=".my-class"
        method="xpath", selector="//div[@id='main']"
    """
    try:
        device = await run_sync(DevicePool().get, req.serial_id)
        if device is None:
            return APIResponse(code=1002, message="device not found")
        element = await run_sync(device.wait_for_element, req.method, req.selector, 3)
        if element is None:
            logging.info("not found element")
            return APIResponse(code=1003, message="element not found")
        logging.info(f"find element : {element}")
        return APIResponse(code=0, message="success", data={"element": str(element)})
    except Exception as e:
        return APIResponse(code=2000, message="系统异常", error=str(e))


@router.post("/find_all", response_model=APIResponse)
async def find_elements(req: FindElementRequest):
    """查找多个元素接口"""
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
        
        elements = await run_sync(device.find_elements, req.method, req.selector)
        # 确保 elements 是列表类型
        if elements is None or not isinstance(elements, list) or len(elements) == 0:
            logging.info("no elements found")
            return APIResponse(
                code=1003, 
                message="elements not found", 
                error=f"No elements found with selector: {req.selector}",
                trace_id=trace_id
            )
        
        # 提取元素信息
        element_data = []
        for i, element in enumerate(elements):
            try:
                element_info = {
                    "index": i,
                    "tag_name": element.tag_name,
                    "text": element.text,
                    "attributes": {
                        "id": element.get_attribute("id"),
                        "class": element.get_attribute("class"),
                        "name": element.get_attribute("name"),
                        "href": element.get_attribute("href"),
                        "src": element.get_attribute("src")
                    }
                }
                element_data.append(element_info)
            except Exception as e:
                logging.warning(f"Failed to extract element {i} info: {e}")
                continue
        
        logging.info(f"found {len(element_data)} elements")
        return APIResponse(
            code=0, 
            message="success", 
            data={
                "elements": element_data,
                "count": len(element_data)
            },
            trace_id=trace_id
        )
    except Exception as e:
        return APIResponse(
            code=2000, 
            message="系统异常", 
            error=str(e),
            trace_id=trace_id
        )


@router.post("/click", response_model=APIResponse)
async def click(req: ClickRequest):
    """点击元素接口"""
    trace_id = gen_trace_id()
    try:
        device = await run_sync(DevicePool().get, req.serial_id)
        if device is None:
            # 创建 ConnectConfig 对象
            from hybrid_driver.api.models import ConnectConfig
            config = ConnectConfig(
                serial_id=req.serial_id,
                user_id="0",  # 默认用户ID
                android_process="com.tencent.mm:appbrand0"
            )
            device = await run_sync(DevicePool().connect, config)
            if device is None:
                return APIResponse(
                    code=1002, 
                    message="设备未找到或连接失败", 
                    error=f"Device {req.serial_id} not found or connection failed",
                    trace_id=trace_id
                )
        if not hasattr(device, '_web_execute') or device._web_execute is None:
            return APIResponse(
                code=1004, 
                message="WebDriver未初始化", 
                error="WebDriver not initialized",
                trace_id=trace_id
            )
        #
        # try:
        #     pages = await run_sync(device._web_execute.get_visible_pages)
        #     # 强制类型安全，pages 只允许为 list，否则置空
        #     if not isinstance(pages, list):
        #         pages = []
        #     # 只保留真正的页面对象（可选：可加更严格的类型检查）
        #     if len(pages) == 0:
        #         return APIResponse(
        #             code=1006,
        #             message="没有可用的页面",
        #             error="No available pages found",
        #             trace_id=trace_id
        #         )
        #     # 只遍历 list 类型
        #     page0 = pages[0]
        #     await run_sync(device._web_execute.switch_to_window, getattr(page0, 'handle', page0))
        # except Exception as e:
        #     return APIResponse(
        #         code=1007,
        #         message="页面切换失败",
        #         error=f"Failed to switch to page: {str(e)}",
        #         trace_id=trace_id
        #     )
        #
        try:
            from hybrid_driver.operation import Click
            click_op = Click(
                method=req.method,
                selector=req.selector,
                timeout=req.timeout or 10,
                wait_for_new_window=req.wait_for_new_window or False,
                context_type="WEB"
            )
            result = await run_sync(click_op.execute, device)
            if result:
                return APIResponse(
                    code=0, 
                    message="点击操作成功", 
                    data={"method": req.method, "selector": req.selector},
                    trace_id=trace_id
                )
            else:
                return APIResponse(
                    code=1003, 
                    message="点击操作失败", 
                    error="Click operation returned false",
                    trace_id=trace_id
                )
        except Exception as e:
            error_msg = str(e)
            if "element not found" in error_msg.lower() or "no such element" in error_msg.lower():
                return APIResponse(
                    code=1008, 
                    message="元素未找到", 
                    error=f"Element not found: {error_msg}",
                    data={"method": req.method, "selector": req.selector},
                    trace_id=trace_id
                )
            elif "element not interactable" in error_msg.lower() or "element click intercepted" in error_msg.lower():
                return APIResponse(
                    code=1009, 
                    message="元素不可交互", 
                    error=f"Element not interactable: {error_msg}",
                    data={"method": req.method, "selector": req.selector},
                    trace_id=trace_id
                )
            elif "timeout" in error_msg.lower():
                return APIResponse(
                    code=1010, 
                    message="操作超时", 
                    error=f"Operation timeout: {error_msg}",
                    data={"method": req.method, "selector": req.selector, "timeout": req.timeout},
                    trace_id=trace_id
                )
            else:
                return APIResponse(
                    code=1011, 
                    message="点击操作异常", 
                    error=f"Click operation exception: {error_msg}",
                    data={"method": req.method, "selector": req.selector},
                    trace_id=trace_id
                )
    except Exception as e:
        return APIResponse(
            code=2000, 
            message="系统异常", 
            error=f"System exception: {str(e)}",
            trace_id=trace_id
        )


@router.post("/operations", response_model=APIResponse)
async def run_operations(req: OperationRequest):
    """执行操作序列"""
    trace_id = gen_trace_id()
    device = await run_sync(DevicePool().get, req.serial_id)
    if not device:
        return APIResponse(code=400101, message="device not found", trace_id=trace_id)
    try:
        ops = build_operations([op.model_dump() for op in req.operations])
    except AttributeError as e:
        # 如果 operations 中的某些项不是 Pydantic 模型，尝试转换为字典
        operation_dicts = []
        for op in req.operations:
            try:
                if hasattr(op, 'model_dump'):
                    operation_dicts.append(op.model_dump())
                else:
                    # 尝试将对象转换为字典
                    operation_dicts.append(dict(op))
            except Exception as e2:
                logging.error(f"无法转换操作对象: {op}, 错误: {e2}")
                return APIResponse(
                    code=2000, 
                    message="系统异常", 
                    error=f"无法处理操作对象: {str(e2)}",
                    trace_id=trace_id
                )
        ops = build_operations(operation_dicts)
    seq = OperationSequence(ops)
    results = await run_sync(seq.execute, device)
    return APIResponse(code=0, message="success", data={"results": results}, trace_id=trace_id)


@router.post("/run_script",response_model=APIResponse)
async def run_script(req: RunScript):
    pass