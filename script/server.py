import logging
from typing import Optional, Any

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import JSONResponse

from device_pool import DevicePool
from web_driver import SeleniumWebDriver

app = FastAPI()
device_pool = DevicePool(driver_cls=SeleniumWebDriver)

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


@app.post("/connect", response_model=APIResponse)
def connect(req: ConnectRequest):
    try:
        device = device_pool.connect(req.serial_id)
        if device is not None:
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

    device.find_element()
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
        element = device.find_element(req.method, req.selector)
        if element is None:
            return APIResponse(code=1003, message="element not found")
        logging.info(f"find element : {element}")
        return APIResponse(code=0, message="success", data={"element": str(element)})
    except Exception as e:
        return APIResponse(code=2000, message="系统异常", error=str(e))
