from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class ConnectRequest(BaseModel):
    serial_id: str
    user_id: str
    android_process: str


class ConnectConfig(BaseModel):
    """设备连接配置"""
    serial_id: str = Field(description="设备序列号")
    user_id: str = Field(description="用户ID")
    ip: Optional[str] = Field(default=None, description="设备IP地址")
    port: Optional[int] = Field(default=None, description="设备端口")
    executor_type: str = Field(default="selenium", description="执行器类型")
    timeout: int = Field(default=30, description="连接超时时间")
    webdriver_mode: str = Field(default="remote", description="WebDriver模式")
    remote_url: Optional[str] = Field(default=None, description="远程WebDriver地址")
    browser_version: Optional[str] = Field(default="138", description="浏览器版本")
    platform_name: Optional[str] = Field(default="linux", description="平台名称")
    android_package: Optional[str] = Field(default="com.tencent.mm", description="Android包名")
    android_process: Optional[str] = Field(default="com.tencent.mm:appbrand0", description="Android进程名")


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


# 响应数据模型
class DeviceInfo(BaseModel):
    """设备信息"""
    platform: str = Field(default="android", description="平台类型")
    webdriver_type: str = Field(default="selenium", description="WebDriver类型")
    connection_time: Optional[datetime] = Field(default=None, description="连接时间")


class DeviceCapabilities(BaseModel):
    """设备能力信息"""
    browser_name: str = Field(default="chrome", description="浏览器名称")
    platform_name: str = Field(default="android", description="平台名称")
    browser_version: Optional[str] = Field(default=None, description="浏览器版本")


class ConnectionData(BaseModel):
    """连接成功返回的数据"""
    session_id: str = Field(description="WebDriver会话ID")
    serial_id: str = Field(description="设备序列号")
    user_id: str = Field(description="用户ID")
    status: str = Field(default="connected", description="连接状态")
    device_info: DeviceInfo = Field(description="设备信息")
    capabilities: DeviceCapabilities = Field(description="设备能力")


class ErrorData(BaseModel):
    """错误信息数据"""
    serial_id: str = Field(description="设备序列号")
    error_reason: str = Field(description="错误原因")
    suggestions: List[str] = Field(default=[], description="解决建议")
    exception_type: Optional[str] = Field(default=None, description="异常类型")
    error_details: Optional[str] = Field(default=None, description="详细错误信息")


class DisconnectData(BaseModel):
    """断开连接返回的数据"""
    serial_id: str = Field(description="设备序列号")
    status: str = Field(description="断开状态")
    disconnect_time: Optional[datetime] = Field(default=None, description="断开时间")


class ActionData(BaseModel):
    """操作执行返回的数据"""
    serial_id: str = Field(description="设备序列号")
    action_type: str = Field(description="操作类型")
    params: Optional[Dict[str, Any]] = Field(default=None, description="操作参数")
    status: str = Field(description="执行状态")
    result: str = Field(description="执行结果")
    execution_time: Optional[datetime] = Field(default=None, description="执行时间")


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

class RunScript(BaseModel):
    serial_id: str
    script: str
    timeout: Optional[int] = 10
    wait_for_new_window: Optional[bool] = False


class GetTextRequest(BaseModel):
    serial_id: str
    method: str
    selector: str
    timeout: Optional[int] = 10