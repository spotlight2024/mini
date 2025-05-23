from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from webdriver.web_driver import SeleniumWebDriver
from device import DeviceManager

app = FastAPI()
driver = SeleniumWebDriver()
device_manager = DeviceManager()

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
    selector: str

@app.post("/connect")
def connect(req: ConnectRequest):
    device_manager.add_device(req.serial_id, req.ip, req.port)
    success = driver.connect(req.serial_id, req.ip, req.port)
    if success:
        return {"code": "success", "message": "连接成功"}
    else:
        return {"code": "fail", "message": "连接失败"}

@app.post("/action")
def action(req: ActionRequest):
    result = driver.action(req.serial_id, req.type, req.params)
    return result

@app.post("/findElement")
def find_element(req: FindElementRequest):
    result = driver.find_element(req.serial_id, req.selector)
    return result 