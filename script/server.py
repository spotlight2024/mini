import logging
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import JSONResponse

from device_pool import DevicePool

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


@app.post("/connect")
def connect(req: ConnectRequest):
    try:
        device = device_pool.connect(req.serial_id)
    except Exception as ex:
        return JSONResponse(status_code=404, content={"error": str(ex)})

    if device is not None:
        return JSONResponse(status_code=200, content={"message":"success"})
    else:
        return JSONResponse(status_code=404, content={"code": "fail", "message": "连接失败"})


@app.post("/disconnect")
def disconnect(req: DisconnectRequest):
    device = device_pool.get(req.serial_id)
    if device is None:
        return JSONResponse(status_code=404, content={"error": "device not found"})
    else:
        device.disconnect()
        return JSONResponse(status_code=200, content={"message":"success"})

@app.post("/action")
def action(req: ActionRequest):
    device = device_pool.get(req.serial_id)
    if device is None:
        return JSONResponse(status_code=404, content={"error": "device not found"})

    device.find_element()
    return JSONResponse({"code": "success", "message": req.session_id})


@app.post("/find_element")
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
        logging.info()
        element = device.find_element(req.method,req.selector)
        if element is None:
            return JSONResponse(status_code=404, content={"error": "element not found"})
        logging.info(f"find element : {element}")
        return JSONResponse(status_code=200, content={"ok": True})
    except Exception as e:
        return JSONResponse(status_code=403, content={"error": str(e)})
