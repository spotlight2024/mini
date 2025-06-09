from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from starlette.responses import JSONResponse

from device import DeviceManager
from web_driver import SeleniumWebDriver

app = FastAPI()
driver = SeleniumWebDriver()
device_manager = DeviceManager()

class SessionRequest(BaseModel):
    session_id: str
    android_process: str
    android_package: str

class ConnectRequest(BaseModel):
    serial_id: str
    ip: str
    port: int

class ActionRequest(BaseModel):
    serial_id: str
    type: str
    params: Optional[dict] = {}

class FindElementRequest(BaseModel):
    serial_id: str
    method: str
    selector: str

@app.post("/createSession/")
def create_session(request: ConnectRequest):
    pass

@app.post("/connect")
def connect(req: ConnectRequest):
    device_manager.add_device(req.serial_id)
    success = driver.connect(req.serial_id)
    if success:
        return JSONResponse({"code": "success", "message": "连接成功"})
    else:
        return JSONResponse({"code": "fail", "message": "连接失败"})

@app.post("/action")
def action(req: ActionRequest):
    result = driver.action(req.serial_id, req.type, req.params)
    return result

@app.post("/findElement")
def find_element(req: FindElementRequest):
    try:
        device_manager.get_device(req.serial_id)
        result = driver.find_element(req.method, req.selector)
        # 如果 result 已经是 dict 并包含 code/message，直接返回
        if isinstance(result, dict) and 'code' in result:
            return result
        # 否则包装为成功返回
        return {"code": "success", "result": result}
    except Exception as e:
        # 捕获所有异常，返回详细异常信息
        return {
            "code": "fail",
            "message": str(e),
            "exception_type": type(e).__name__,
        } 

@app.get("/")
def root():
    return {"message": "服务已启动"}