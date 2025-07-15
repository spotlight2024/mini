from typing import Optional, Any, List
from pydantic import BaseModel


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