import logging
from typing import Optional, Any, List
import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import JSONResponse

from device_pool import DevicePool
from web_driver import SeleniumWebDriver
from operation import OperationSequence, FindElement, Click, Wait, JS, HandlePopup, build_operations

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


class OperationItem(BaseModel):
    type: str
    method: Optional[str] = None
    selector: Optional[str] = None
    timeout: Optional[int] = 10
    seconds: Optional[int] = None
    script: Optional[str] = None
    popup_selector: Optional[str] = None


class OperationRequest(BaseModel):
    serial_id: str
    operations: List[OperationItem]


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


def gen_trace_id():
    return str(uuid.uuid4())


@app.post("/run_operations", response_model=APIResponse)
def run_operations(req: OperationRequest):
    """
    {
  "serial_id": "JJGICIN7QOAELNGI",
  "operations": [
    {
      "type": "find",
      "method": "css selector",
      "selector": ".first-btn",
      "timeout": 10
    },
    {
      "type": "click",
      "method": "css selector",
      "selector": ".first-btn",
      "timeout": 10
    },
    {
      "type": "find",
      "method": "css selector",
      "selector": ".second-btn",
      "timeout": 10
    },
    {
      "type": "click",
      "method": "css selector",
      "selector": ".second-btn",
      "timeout": 10
    }
  ]
}
    :param req:
    :return:
    """
    trace_id = gen_trace_id()
    device = device_pool.get(req.serial_id)
    if not device:
        return APIResponse(code=400101, message="device not found", trace_id=trace_id)
    ops = build_operations([op.model_dump() for op in req.operations])
    seq = OperationSequence(ops)
    results = seq.run(device, trace_id=trace_id)
    return APIResponse(code=0, message="success", data={"results": results}, trace_id=trace_id)

if __name__ == "__main__":
    connect(ConnectRequest(serial_id="JJGICIN7QOAELNGI"))
    find_element(FindElementRequest(serial_id="JJGICIN7QOAELNGI",method="css selector",selector=".home-coupon"))



