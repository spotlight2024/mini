import logging
from typing import Optional, Any, List
import uuid

from fastapi import FastAPI
from pydantic import BaseModel
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from hybrid_driver.device_pool import DevicePool
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils
from hybrid_driver.operation import OperationSequence, FindElement, Click, Wait, JS, HandlePopup, build_operations, CollectItemsOp

app = FastAPI()
device_pool = DevicePool()


class ConnectRequest(BaseModel):
    serial_id: str


class DisconnectRequest(BaseModel):
    serial_id: str


class ActionRequest(BaseModel):
    serial_id: str
    type: str
    params: Optional[dict] = {}


class FindElementRequest(BaseModel):
    serial_id: str
    method: str
    selector: str


class APIResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None


class OperationItem(BaseModel):
    type: str
    method: Optional[str] = None
    selector: Optional[str] = None
    timeout: Optional[int] = 10
    seconds: Optional[int] = None
    script: Optional[str] = None
    popup_selector: Optional[str] = None
    wait_for_new_window: Optional[bool] = False
    wait_for_render: Optional[bool] = True


class OperationRequest(BaseModel):
    serial_id: str
    operations: List[OperationItem]


class ClickRequest(BaseModel):
    serial_id: str
    method: str
    selector: str
    timeout: Optional[int] = 10
    wait_for_new_window: Optional[bool] = False


class SetTextRequest(BaseModel):
    serial_id: str
    method: str
    selector: str
    text: str
    timeout: Optional[int] = 10


@app.post("/connect", response_model=APIResponse)
def connect(req: ConnectRequest):
    try:
        device = device_pool.connect(req.serial_id)
        if device is not None:
            driver = device._web_execute._driver

            pages = WebDriverUtils.get_visible_page(driver)
            driver.switch_to.window(pages[0].handle)
            return APIResponse(code=0, message="success")
        else:
            return APIResponse(code=1001, message="连接失败")
    except Exception as ex:
        return APIResponse(code=2000, message="系统异常", error=str(ex))


@app.post("/disconnect", response_model=APIResponse)
def disconnect(req: DisconnectRequest):
    device = device_pool.get(req.serial_id)
    if device is None:
        return APIResponse(code=1002, message="device not found")
    else:
        device.disconnect()
        return APIResponse(code=0, message="success")


@app.post("/action", response_model=APIResponse)
def action(req: ActionRequest):
    device = device_pool.get(req.serial_id)
    if device is None:
        return APIResponse(code=1002, message="device not found")

    # TODO: 实现具体的action逻辑
    return APIResponse(code=0, message="success")


@app.post("/find_element", response_model=APIResponse)
def find_element(req: FindElementRequest):
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
        device = device_pool.get(req.serial_id)
        if device is None:
            return APIResponse(code=1002, message="device not found")
        element = device.wait_for_element(req.method, req.selector,timeout=3)
        if element is None:
            logging.info("not found element")
            return APIResponse(code=1003, message="element not found")
        logging.info(f"find element : {element}")
        return APIResponse(code=0, message="success", data={"element": str(element)})
    except Exception as e:
        return APIResponse(code=2000, message="系统异常", error=str(e))


def gen_trace_id():
    return str(uuid.uuid4())


@app.post("/click", response_model=APIResponse)
def click(req: ClickRequest):
    """
    点击元素接口
    """
    trace_id = gen_trace_id()
    try:
        # 1. 检查设备连接状态
        device = device_pool.get(req.serial_id)
        if device is None:
            # 尝试自动连接设备
            device = device_pool.connect(req.serial_id)
            if device is None:
                return APIResponse(
                    code=1002, 
                    message="设备未找到或连接失败", 
                    error=f"Device {req.serial_id} not found or connection failed",
                    trace_id=trace_id
                )

        # 2. 检查WebDriver状态
        if not hasattr(device, '_web_execute') or device._web_execute is None:
            return APIResponse(
                code=1004, 
                message="WebDriver未初始化", 
                error="WebDriver not initialized",
                trace_id=trace_id
            )

        driver = device._web_execute._driver
        if driver is None:
            return APIResponse(
                code=1005, 
                message="WebDriver实例为空", 
                error="WebDriver instance is null",
                trace_id=trace_id
            )

        # 3. 检查页面状态
        try:
            pages = WebDriverUtils.get_visible_page(driver)
            if not pages:
                return APIResponse(
                    code=1006, 
                    message="没有可用的页面", 
                    error="No available pages found",
                    trace_id=trace_id
                )
            driver.switch_to.window(pages[0].handle)
        except Exception as e:
            return APIResponse(
                code=1007, 
                message="页面切换失败", 
                error=f"Failed to switch to page: {str(e)}",
                trace_id=trace_id
            )

        # 4. 创建并执行Click操作
        try:
            click_op = Click(
                method=req.method,
                selector=req.selector,
                timeout=req.timeout or 10,
                wait_for_new_window=req.wait_for_new_window or False,
                context_type="WEB"
            )
            
            # 执行点击操作
            result = click_op.execute(device)
            
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

@app.post("/run_operations", response_model=APIResponse)
def run_operations(req: OperationRequest):
    trace_id = gen_trace_id()
    device = device_pool.get(req.serial_id)
    if not device:
        return APIResponse(code=400101, message="device not found", trace_id=trace_id)
    ops = build_operations([op.model_dump() for op in req.operations])
    seq = OperationSequence(ops)
    results = seq.execute(device)
    return APIResponse(code=0, message="success", data={"results": results}, trace_id=trace_id)


@app.post("/check_page")
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
        device = device_pool.get(serial_id)
        if device is None:
            return {"code": 2, "message": f"Device {serial_id} not found"}
        
        try:
            # 获取当前页面信息
            current_url = device.get_current_url()
            page_source = device.get_page_source()
            
            # 简单的页面检测逻辑，可以根据需要扩展
            is_current_page = check_page_type(current_url, page_source, required_page)
            
            return {
                "code": 0,
                "message": "Page check completed",
                "isCurrentPage": is_current_page,
                "currentPage": detect_current_page(current_url, page_source),
                "currentUrl": current_url
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

def check_page_type(url: str, page_source: str, required_page: str) -> bool:
    """检查页面类型"""
    try:
        # 根据URL和页面内容判断页面类型
        if required_page == "Home":
            # 检查是否为首页
            if "home" in url.lower() or "index" in url.lower():
                return True
            # 检查页面源码中是否包含首页特征
            if any(keyword in page_source.lower() for keyword in ["首页", "主页", "home", "menu_page"]):
                return True
        
        elif required_page == "ShopDetail":
            # 检查是否为店铺详情页
            if "shop" in url.lower() or "store" in url.lower():
                return True
            # 检查页面源码中是否包含店铺详情页特征
            if any(keyword in page_source.lower() for keyword in ["店铺", "商店", "shop", "store", "商品"]):
                return True
        
        elif required_page == "SearchShopList":
            # 检查是否为店铺搜索页
            if "search" in url.lower():
                return True
            if any(keyword in page_source.lower() for keyword in ["搜索", "search", "店铺列表"]):
                return True
        
        # 更多页面类型可以在此扩展
        
        return False
        
    except Exception as e:
        logging.error(f"Page type check failed: {str(e)}")
        return False

def detect_current_page(url: str, page_source: str) -> str:
    """检测当前页面类型"""
    try:
        # 根据URL和页面内容检测当前页面
        if "home" in url.lower() or "index" in url.lower():
            return "Home"
        elif "shop" in url.lower() or "store" in url.lower():
            return "ShopDetail"
        elif "search" in url.lower():
            return "SearchShopList"
        
        # 根据页面内容检测
        if any(keyword in page_source.lower() for keyword in ["首页", "主页", "menu_page"]):
            return "Home"
        elif any(keyword in page_source.lower() for keyword in ["店铺", "商店", "商品列表"]):
            return "ShopDetail"
        elif any(keyword in page_source.lower() for keyword in ["搜索", "店铺列表"]):
            return "SearchShopList"
        
        return "Unknown"
        
    except Exception as e:
        logging.error(f"Page detection failed: {str(e)}")
        return "Unknown"

@app.post("/find_elements", response_model=APIResponse)
def find_elements(req: FindElementRequest):
    """
    查找多个元素接口
    """
    trace_id = gen_trace_id()
    try:
        device = device_pool.get(req.serial_id)
        if device is None:
            return APIResponse(
                code=1002, 
                message="设备未找到", 
                error=f"Device {req.serial_id} not found",
                trace_id=trace_id
            )
        
        elements = device.find_elements(req.method, req.selector)
        if elements is None or len(elements) == 0:
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


class CollectItemsRequest(BaseModel):
    serial_id: str
    container_selector: Optional[str] = None
    item_selectors: Optional[dict] = None
    options: Optional[dict] = {}
    filters: Optional[dict] = {}
    dialog_views: Optional[list] = []
    loading_view: Optional[str] = None
    close_dialog: Optional[bool] = True
    package_name: Optional[str] = None
    # 新增：支持新协议JSON配置
    config_json: Optional[str] = None
    config_file: Optional[str] = None


@app.post("/collect_items", response_model=APIResponse)
def collect_items(req: CollectItemsRequest):
    """
    收集元素信息接口 - Web端ACTION_COLLECT_ITEM_INFO实现
    支持新协议JSON配置和老协议参数
    """
    trace_id = gen_trace_id()
    try:
        device = device_pool.get(req.serial_id)
        if device is None:
            return APIResponse(
                code=1002, 
                message="设备未找到", 
                error=f"Device {req.serial_id} not found",
                trace_id=trace_id
            )
        
        # 创建收集操作，支持新协议和老协议
        if req.config_json or req.config_file:
            # 使用新协议JSON配置
            collect_op = CollectItemsOp(
                config_json=req.config_json,
                config_file=req.config_file
            )
        else:
            # 使用老协议参数（向后兼容）
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
        result = collect_op.execute(device)
        
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

if __name__ == "__main__":
    serial_id = "172.16.1.125:6524"

    connect(ConnectRequest(serial_id=serial_id))
    # switch to current page
    device = DevicePool().get(serial_id)
    driver = device._web_execute._driver

    pages = WebDriverUtils.get_visible_page(driver)
    driver.switch_to.window(pages[0].handle)

    # click(ClickRequest(serial_id=serial_id,method="css selector",selector="wx-view.query.menu-bar--query"))
    # 1. 等待所有可见的菜单项加载完成
    wait = WebDriverWait(driver, 10)

    products = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR,
        "wx-view.pos-r.list--pos-r.kind_100000.list--kind_100000.two-kind.list--two-kind")  # 每个产品的根容器 :contentReference[oaicite:7]{index=7}
    ))

    # 2. 逐个提取名称和首杯价
    menu_data = []
    for prod in products:
        # 名称：<wx-view class="menu-product_name product--menu-product_name ellipsis product--ellipsis">...</wx-view>
        name_el = prod.find_element(By.CSS_SELECTOR,
            "wx-view.menu-product_name.product--menu-product_name")
        name = name_el.text  # 如 "生椰拿铁（首创）" :contentReference[oaicite:8]{index=8}

        # 首杯价：<wx-view class="discountPrice bar--discountPrice">8.8</wx-view>
        price_el = prod.find_element(By.CSS_SELECTOR,
            "wx-view.discountPrice.bar--discountPrice")
        price = price_el.text  # 如 "8.8" :contentReference[oaicite:9]{index=9}

        menu_data.append((name, price))

    # 3. 输出结果
    for name, price in menu_data:
        print(f"{name} —— ¥{price}")


