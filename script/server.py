from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import JSONResponse

from device_pool import DevicePool
from web_driver import SeleniumWebDriver

app = FastAPI()
driver = SeleniumWebDriver()

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
        device = DevicePool.connect(req.serial_id, req.ip, req.port)
    except Exception as ex:
        return JSONResponse(status_code=404, content={"error": str(ex)})

    if device is None:
        return JSONResponse(status_code=200, content={"ok"})
    else:
        return JSONResponse(status_code=404, content={"code": "fail", "message": "连接失败"})


@app.post("/disconnect")
def disconnect(req: DisconnectRequest):
    device = DevicePool.get(req.serial_id)
    if device is None:
        return JSONResponse(status_code=404, content={"error": "device not found"})
    else:
        device.disconnect()
        return JSONResponse(status_code=200, content={"ok"})

@app.post("/action")
def action(req: ActionRequest):
    device = DevicePool.get(req.serial_id)
    if device is None:
        return JSONResponse(status_code=404, content={"error": "device not found"})

    device.find_element()
    return JSONResponse({"code": "success", "message": req.session_id})


@app.post("/findElement")
def find_element(req: FindElementRequest):
    try:
        DevicePool.get(req.serial_id).find_element(req.selector)
        # 如果 result 已经是 dict 并包含 code/message，直接返回
        return JSONResponse(status_code=200, content={"ok"})
    except Exception as e:
        # 捕获所有异常，返回详细异常信息
        return JSONResponse(status_code=404, content={"error": str(e)})
