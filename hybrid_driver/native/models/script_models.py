"""脚本执行相关的数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class Script(BaseModel):
    """脚本模型"""
    id: str = Field(..., description="脚本ID")
    name: str = Field(..., description="脚本名称")
    commands: str = Field(..., description="脚本命令内容")
    params: Optional[Dict[str, str]] = Field(None, description="脚本参数")
    cancellable: bool = Field(default=False, description="是否可取消")
    version: int = Field(default=1, description="脚本版本")


class ScriptExecuteRequest(BaseModel):
    """脚本执行请求模型"""
    req_id: str = Field(..., description="请求ID")
    ip: str = Field(..., description="目标IP地址")
    port: int = Field(..., description="目标端口", ge=1, le=65535)
    script: Script = Field(..., description="要执行的脚本")


class CommandExecuteRequest(BaseModel):
    """命令执行请求模型"""
    req_id: str = Field(..., description="请求ID")
    command: str = Field(..., description="要执行的命令")


class CommandResult(BaseModel):
    """命令执行结果模型"""
    code: int = Field(..., description="执行结果代码，0表示成功")
    data: Optional[str] = Field(None, description="执行结果数据")
    message: Optional[str] = Field(None, description="执行结果消息")

    def is_success(self) -> bool:
        """判断执行是否成功"""
        return self.code == 0

    def is_failure(self) -> bool:
        """判断执行是否失败"""
        return self.code != 0


class ExecutorContext(BaseModel):
    """执行器上下文模型"""
    params: Dict[str, str] = Field(default_factory=dict, description="参数字典")
    results: List[CommandResult] = Field(default_factory=list, description="执行结果列表")

    class Config:
        arbitrary_types_allowed = True

    def add_result(self, result: CommandResult) -> None:
        """添加执行结果"""
        self.results.append(result)

    def get_last_result(self) -> Optional[CommandResult]:
        """获取最后一个执行结果"""
        return self.results[-1] if self.results else None

    def has_failure(self) -> bool:
        """检查是否有失败的结果"""
        return any(result.is_failure() for result in self.results)

    def get_first_failure(self) -> Optional[CommandResult]:
        """获取第一个失败的结果"""
        for result in self.results:
            if result.is_failure():
                return result
        return None