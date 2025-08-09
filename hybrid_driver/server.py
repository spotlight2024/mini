"""
兼容保留：仅转发 app 实例到新的统一入口。

历史上外部可能通过 "hybrid_driver.server:app" 引用服务入口。
现在统一入口是 "hybrid_driver.server_optimized:app"，
此文件只做兼容转发，避免外部引用立刻崩溃。
"""

from .server_optimized import app  # noqa: F401


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
async def connect(req: ConnectRequest):
    try:
        # 创建 ConnectConfig 对象
        from hybrid_driver.api.models import ConnectConfig

        config = ConnectConfig(
            serial_id=req.serial_id,
            user_id="connect_user",  # 默认用户ID
            android_process="com.tencent.mm:appbrand0",
        )
        device = await run_sync(device_pool.connect, config)
        if device is not None:
            # 使用装饰器模式获取 WebDriver
            # 移除所有 web_driver_decorator 相关代码和注释
            # 保留 WebExecutor 体系和 raw_driver 访问方式
            return APIResponse(code=0, message="success")
        else:
            return APIResponse(code=1001, message="连接失败")
    except Exception as ex:
        return APIResponse(code=2000, message="系统异常", error=str(ex))


@app.post("/disconnect", response_model=APIResponse)
async def disconnect(req: DisconnectRequest):
    device = await run_sync(device_pool.get, req.serial_id)
    if device is None:
        return APIResponse(code=1002, message="device not found")
    else:
        await run_sync(device.disconnect)
        return APIResponse(code=0, message="success")


@app.post("/action", response_model=APIResponse)
async def action(req: ActionRequest):
    device = await run_sync(device_pool.get, req.serial_id)
    if device is None:
        return APIResponse(code=1002, message="device not found")
    # TODO: 实现具体的action逻辑
    return APIResponse(code=0, message="success")


@app.post("/find_element", response_model=APIResponse)
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
        device = await run_sync(device_pool.get, req.serial_id)
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


def gen_trace_id():
    return str(uuid.uuid4())


@app.post("/click", response_model=APIResponse)
async def click(req: ClickRequest):
    """
    点击元素接口
    """
    trace_id = gen_trace_id()
    try:
        device = await run_sync(device_pool.get, req.serial_id)
        if device is None:
            # 创建 ConnectConfig 对象
            from hybrid_driver.api.models import ConnectConfig

            config = ConnectConfig(
                serial_id=req.serial_id,
                user_id="click_user",  # 默认用户ID
                android_process="com.tencent.mm:appbrand0",
            )
            device = await run_sync(device_pool.connect, config)
            if device is None:
                return APIResponse(
                    code=1002,
                    message="设备未找到或连接失败",
                    error=f"Device {req.serial_id} not found or connection failed",
                    trace_id=trace_id,
                )
        if not hasattr(device, "_web_execute") or device._web_execute is None:
            return APIResponse(
                code=1004,
                message="WebDriver未初始化",
                error="WebDriver not initialized",
                trace_id=trace_id,
            )
        # 使用装饰器模式获取 WebDriver
        # 移除所有 web_driver_decorator 相关代码和注释
        # 保留 WebExecutor 体系和 raw_driver 访问方式
        try:
            pages = await run_sync(device._web_execute.get_visible_pages)
            # 强制类型安全，pages 只允许为 list，否则置空
            if not isinstance(pages, list):
                pages = []
            # 只保留真正的页面对象（可选：可加更严格的类型检查）
            if len(pages) == 0:
                return APIResponse(
                    code=1006,
                    message="没有可用的页面",
                    error="No available pages found",
                    trace_id=trace_id,
                )
            # 只遍历 list 类型
            page0 = pages[0]
            await run_sync(
                device._web_execute.switch_to_window, getattr(page0, "handle", page0)
            )
        except Exception as e:
            return APIResponse(
                code=1007,
                message="页面切换失败",
                error=f"Failed to switch to page: {str(e)}",
                trace_id=trace_id,
            )
        try:
            click_op = Click(
                method=req.method,
                selector=req.selector,
                timeout=req.timeout or 10,
                wait_for_new_window=req.wait_for_new_window or False,
                context_type="WEB",
            )
            result = await run_sync(click_op.execute, device)
            if result:
                return APIResponse(
                    code=0,
                    message="点击操作成功",
                    data={"method": req.method, "selector": req.selector},
                    trace_id=trace_id,
                )
            else:
                return APIResponse(
                    code=1003,
                    message="点击操作失败",
                    error="Click operation returned false",
                    trace_id=trace_id,
                )
        except Exception as e:
            error_msg = str(e)
            if (
                "element not found" in error_msg.lower()
                or "no such element" in error_msg.lower()
            ):
                return APIResponse(
                    code=1008,
                    message="元素未找到",
                    error=f"Element not found: {error_msg}",
                    data={"method": req.method, "selector": req.selector},
                    trace_id=trace_id,
                )
            elif (
                "element not interactable" in error_msg.lower()
                or "element click intercepted" in error_msg.lower()
            ):
                return APIResponse(
                    code=1009,
                    message="元素不可交互",
                    error=f"Element not interactable: {error_msg}",
                    data={"method": req.method, "selector": req.selector},
                    trace_id=trace_id,
                )
            elif "timeout" in error_msg.lower():
                return APIResponse(
                    code=1010,
                    message="操作超时",
                    error=f"Operation timeout: {error_msg}",
                    data={
                        "method": req.method,
                        "selector": req.selector,
                        "timeout": req.timeout,
                    },
                    trace_id=trace_id,
                )
            else:
                return APIResponse(
                    code=1011,
                    message="点击操作异常",
                    error=f"Click operation exception: {error_msg}",
                    data={"method": req.method, "selector": req.selector},
                    trace_id=trace_id,
                )
    except Exception as e:
        return APIResponse(
            code=2000,
            message="系统异常",
            error=f"System exception: {str(e)}",
            trace_id=trace_id,
        )


@app.post("/run_operations", response_model=APIResponse)
async def run_operations(req: OperationRequest):
    trace_id = gen_trace_id()
    device = await run_sync(device_pool.get, req.serial_id)
    if not device:
        return APIResponse(code=400101, message="device not found", trace_id=trace_id)
    try:
        ops = build_operations([op.model_dump() for op in req.operations])
    except AttributeError as e:
        # 如果 operations 中的某些项不是 Pydantic 模型，尝试转换为字典
        operation_dicts = []
        for op in req.operations:
            try:
                if hasattr(op, "model_dump"):
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
                    trace_id=trace_id,
                )
        ops = build_operations(operation_dicts)
    seq = OperationSequence(ops)
    results = await run_sync(seq.execute, device)
    return APIResponse(
        code=0, message="success", data={"results": results}, trace_id=trace_id
    )


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
        device = await run_sync(device_pool.get, serial_id)
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
            is_current_page = check_page_type(
                current_url_str, page_source_str, required_page
            )

            return {
                "code": 0,
                "message": "Page check completed",
                "isCurrentPage": is_current_page,
                "currentPage": detect_current_page(current_url_str, page_source_str),
                "currentUrl": current_url_str,
            }

        except Exception as e:
            logging.error(f"Page check failed: {str(e)}")
            return {"code": 3, "message": f"Page check error: {str(e)}"}

    except Exception as e:
        logging.error(f"Check page request failed: {str(e)}")
        return {"code": 4, "message": f"Request processing error: {str(e)}"}


def check_page_type(url: str, page_source: str, required_page: str) -> bool:
    """检查页面类型"""
    try:
        # 根据URL和页面内容判断页面类型
        if required_page == "Home":
            # 检查是否为首页
            if "home" in url.lower() or "index" in url.lower():
                return True
            # 检查页面源码中是否包含首页特征
            if any(
                keyword in page_source.lower()
                for keyword in ["首页", "主页", "home", "menu_page"]
            ):
                return True

        elif required_page == "ShopDetail":
            # 检查是否为店铺详情页
            if "shop" in url.lower() or "store" in url.lower():
                return True
            # 检查页面源码中是否包含店铺详情页特征
            if any(
                keyword in page_source.lower()
                for keyword in ["店铺", "商店", "shop", "store", "商品"]
            ):
                return True

        elif required_page == "SearchShopList":
            # 检查是否为店铺搜索页
            if "search" in url.lower():
                return True
            if any(
                keyword in page_source.lower()
                for keyword in ["搜索", "search", "店铺列表"]
            ):
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
        if any(
            keyword in page_source.lower() for keyword in ["首页", "主页", "menu_page"]
        ):
            return "Home"
        elif any(
            keyword in page_source.lower() for keyword in ["店铺", "商店", "商品列表"]
        ):
            return "ShopDetail"
        elif any(keyword in page_source.lower() for keyword in ["搜索", "店铺列表"]):
            return "SearchShopList"

        return "Unknown"

    except Exception as e:
        logging.error(f"Page detection failed: {str(e)}")
        return "Unknown"


@app.post("/find_elements", response_model=APIResponse)
async def find_elements(req: FindElementRequest):
    """
    查找多个元素接口
    """
    trace_id = gen_trace_id()
    try:
        device = await run_sync(device_pool.get, req.serial_id)
        if device is None:
            return APIResponse(
                code=1002,
                message="设备未找到",
                error=f"Device {req.serial_id} not found",
                trace_id=trace_id,
            )

        elements = await run_sync(device.find_elements, req.method, req.selector)
        # 确保 elements 是列表类型
        if elements is None or not isinstance(elements, list) or len(elements) == 0:
            logging.info("no elements found")
            return APIResponse(
                code=1003,
                message="elements not found",
                error=f"No elements found with selector: {req.selector}",
                trace_id=trace_id,
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
                        "src": element.get_attribute("src"),
                    },
                }
                element_data.append(element_info)
            except Exception as e:
                logging.warning(f"Failed to extract element {i} info: {e}")
                continue

        logging.info(f"found {len(element_data)} elements")
        return APIResponse(
            code=0,
            message="success",
            data={"elements": element_data, "count": len(element_data)},
            trace_id=trace_id,
        )
    except Exception as e:
        return APIResponse(
            code=2000, message="系统异常", error=str(e), trace_id=trace_id
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
async def collect_items(req: CollectItemsRequest):
    """
    收集元素信息接口 - Web端ACTION_COLLECT_ITEM_INFO实现
    支持新协议JSON配置和老协议参数
    """
    trace_id = gen_trace_id()
    try:
        device = await run_sync(device_pool.get, req.serial_id)
        if device is None:
            return APIResponse(
                code=1002,
                message="设备未找到",
                error=f"Device {req.serial_id} not found",
                trace_id=trace_id,
            )

        # 创建收集操作，支持新协议和老协议
        if req.config_json or req.config_file:
            collect_op = CollectItemsOp(
                config_json=req.config_json, config_file=req.config_file
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
                package_name=req.package_name,
            )

        # 执行收集操作
        result = await run_sync(collect_op.execute, device)

        if result:
            return APIResponse(
                code=0, message="收集成功", data=result, trace_id=trace_id
            )
        else:
            return APIResponse(
                code=1003,
                message="收集失败",
                error="No items collected",
                trace_id=trace_id,
            )

    except Exception as e:
        return APIResponse(
            code=2000, message="系统异常", error=str(e), trace_id=trace_id
        )


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/mock_click", response_model=APIResponse)
async def mock_click(req: ClickRequest):
    delay = random.uniform(5, 30)
    start = time.time()
    logging.info(f"收到 mock_click 请求: {req.dict()}，模拟耗时 {delay:.2f} 秒")
    await asyncio.sleep(delay)
    end = time.time()
    process_time = end - start
    logging.info(
        f"mock_click 处理完成，delay={delay:.2f}，process_time={process_time:.2f}"
    )
    return APIResponse(
        code=0,
        message=f"模拟点击成功，耗时{delay:.2f}秒",
        data={
            "method": req.method,
            "selector": req.selector,
            "mock_delay": delay,
            "process_time": process_time,
        },
    )


@app.post("/mock_find_element", response_model=APIResponse)
async def mock_find_element(req: FindElementRequest):
    delay = random.uniform(5, 30)
    start = time.time()
    logging.info(f"收到 mock_find_element 请求: {req.dict()}，模拟耗时 {delay:.2f} 秒")
    await asyncio.sleep(delay)
    end = time.time()
    process_time = end - start
    logging.info(
        f"mock_find_element 处理完成，delay={delay:.2f}，process_time={process_time:.2f}"
    )
    return APIResponse(
        code=0,
        message=f"模拟查找元素成功，耗时{delay:.2f}秒",
        data={
            "element": f"mock_element_{req.selector}",
            "mock_delay": delay,
            "process_time": process_time,
        },
    )


if __name__ == "__main__":

    async def main():
        serial_id = "47.94.130.125:6521"

        # 等待连接操作完成
        await connect(ConnectRequest(serial_id=serial_id))
        logger.debug("test")

        # switch to current page
        device = await run_sync(device_pool.get, serial_id)
        if device is None:
            logger.error("设备未找到")
            return

        # 获取可见页面并切换
        driver: SeleniumWebExecutor = device.web_executor
        if driver is None:
            logger.error("WebExecutor未初始化")
            return
        pages = await run_sync(driver.get_visible_pages)
        if pages and isinstance(pages, list) and len(pages) > 0:
            await run_sync(driver.switch_to_window, pages[0].handle)
            logger.info(f"成功切换到页面: {pages[0].handle}")
        else:
            logger.warning("没有找到可见页面")

        find_element = driver.get_raw_remote_webdriver().find_element(
            By.CSS_SELECTOR, "wx-view.search-text"
        )
        logger.info(f"find element : ${find_element.text}")
        find_element.click()

    # 运行异步主函数
    asyncio.run(main())
