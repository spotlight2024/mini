"""执行器相关异常定义"""

from typing import Optional
from ..models.script_models import CommandResult


class ExecutorException(Exception):
    """执行器基础异常"""

    def __init__(self, message: str, result: Optional[CommandResult] = None):
        super().__init__(message)
        self.message = message
        self.result = result or CommandResult(code=1, message=message)


class ScriptExecutionException(ExecutorException):
    """脚本执行异常"""
    pass


class CommandExecutionException(ExecutorException):
    """命令执行异常"""
    pass


class NetworkException(ExecutorException):
    """网络相关异常"""
    pass


class SandboxException(ExecutorException):
    """沙盒执行异常"""
    pass


class VariableReplacementException(ExecutorException):
    """变量替换异常"""
    pass


class HttpRequestException(ExecutorException):
    """HTTP请求异常"""
    pass