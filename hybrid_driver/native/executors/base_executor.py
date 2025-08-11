"""执行器基类"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..models.script_models import CommandResult, ExecutorContext


class BaseExecutor(ABC):
    """执行器基类，定义执行器的通用接口"""

    def __init__(self, context: Optional[ExecutorContext] = None):
        """
        初始化执行器

        Args:
            context: 执行器上下文
        """
        self.context = context or ExecutorContext()

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        执行操作的抽象方法

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Any: 执行结果
        """
        pass

    def get_context(self) -> ExecutorContext:
        """
        获取执行器上下文

        Returns:
            ExecutorContext: 执行器上下文
        """
        return self.context

    def add_result(self, result: CommandResult) -> None:
        """
        添加执行结果到上下文

        Args:
            result: 命令执行结果
        """
        self.context.add_result(result)

    def get_last_result(self) -> Optional[CommandResult]:
        """
        获取最后一个执行结果

        Returns:
            Optional[CommandResult]: 最后一个执行结果
        """
        return self.context.get_last_result()

    def has_failure(self) -> bool:
        """
        检查是否有失败的结果

        Returns:
            bool: 有失败结果返回True
        """
        return self.context.has_failure()

    def get_first_failure(self) -> Optional[CommandResult]:
        """
        获取第一个失败的结果

        Returns:
            Optional[CommandResult]: 第一个失败的结果
        """
        return self.context.get_first_failure()

    def clear_results(self) -> None:
        """清空所有执行结果"""
        self.context.results.clear()

    def get_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取参数值

        Args:
            name: 参数名
            default: 默认值

        Returns:
            Optional[str]: 参数值
        """
        return self.context.params.get(name, default)

    def set_param(self, name: str, value: str) -> None:
        """
        设置参数值

        Args:
            name: 参数名
            value: 参数值
        """
        self.context.params[name] = value

    def get_all_params(self) -> Dict[str, str]:
        """
        获取所有参数

        Returns:
            Dict[str, str]: 参数字典
        """
        return self.context.params.copy()

    def update_params(self, params: Dict[str, str]) -> None:
        """
        更新参数

        Args:
            params: 新的参数字典
        """
        self.context.params.update(params)


class CommandExecutorInterface(BaseExecutor):
    """命令执行器接口"""

    @abstractmethod
    async def execute_command(self, command: str) -> CommandResult:
        """
        执行单个命令

        Args:
            command: 要执行的命令

        Returns:
            CommandResult: 命令执行结果
        """
        pass


class ScriptExecutorInterface(BaseExecutor):
    """脚本执行器接口"""

    @abstractmethod
    async def execute_script(self, commands: str) -> str:
        """
        执行脚本

        Args:
            commands: 脚本命令

        Returns:
            str: 执行结果
        """
        pass