"""沙盒环境中的函数式API包装器"""

from typing import Optional, List, Dict, Any, Union
from ..models.script_models import CommandResult


class BaseSandboxFunction:
    """沙盒函数基类"""

    def __init__(self, command_executor):
        """
        初始化函数包装器

        Args:
            command_executor: 命令执行器
        """
        self.execute_command = command_executor

    def _execute_action(self, action: str, anonymous_param: Optional[str] = None, **kwargs) -> CommandResult:
        """执行动作命令"""
        cmd_parts = [action]

        # 添加其他参数
        for key, value in kwargs.items():
            if isinstance(value, bool):
                if value:
                    cmd_parts.append(f"--{key}=1")
            elif key == "dialog_view":
                if isinstance(value, List):
                    value = '||'.join(value)
                if value:
                    cmd_parts.append(f"--{key}={value}")
            else:
                if value:
                    cmd_parts.append(f"--{key}={value}")

        # 添加匿名参数
        if anonymous_param:
            cmd_parts.append(anonymous_param)

        command = ' '.join(cmd_parts)
        return self.execute_command(command)


class ClickFunction(BaseSandboxFunction):
    """点击操作函数"""

    def __call__(self,
                 pkg: str,
                 id: Optional[str] = None,
                 text: Optional[str] = None,
                 on_fail: Optional[str] = None,
                 retry_timeout: Optional[int] = None,
                 idle_timeout: Optional[int] = None,
                 dialog_view: Optional[Union[List[str], str]] = None,
                 close_dialog_with_ai: bool = False,
                 **kwargs) -> CommandResult:
        """
        点击操作

        Args:
            id: 元素ID
            text: 元素文本
            xpath: XPath选择器
            close_dialog_with_ai: 是否关闭对话框
            pkg: 包名
            **kwargs: 其他参数

        Returns:
            CommandResult: 执行结果
        """
        params = {
            'pkg': pkg,
            'id': id,
            'text': text,
            'on_fail': on_fail,
            'retry_timeout': retry_timeout,
            'idle_timeout': idle_timeout,
            'dialog_view': dialog_view,
            'close_dialog': close_dialog_with_ai,
            **kwargs
        }
        return self._execute_action('ACTION_CLICK', **params)


class TestFunction(BaseSandboxFunction):
    """测试操作"""

    def __call__(self,
                 pkg: str,
                 id: Optional[str] = None,
                 text: Optional[str] = None,
                 error_code: Optional[int] = None,
                 retry_timeout: Optional[int] = None,
                 idle_timeout: Optional[int] = None,
                 dialog_view: Optional[Union[List[str], str]] = None,
                 close_dialog_with_ai: bool = False,
                 **kwargs) -> CommandResult:
        """
        测试操作

        Args:
            pkg: 包名
            id: 元素ID
            text: 元素文本
            error_code: 错误码
            retry_timeout: 重试超时时间
            idle_timeout: 空闲超时时间
            dialog_view: 要关闭的对话框
            close_dialog_with_ai: 是否关闭对话框
            **kwargs: 其他参数

        Returns:
            CommandResult: 执行结果
        """
        params = {
            'pkg': pkg,
            'id': id,
            'text': text,
            'error_code': error_code,
            'retry_timeout': retry_timeout,
            'idle_timeout': idle_timeout,
            'dialog_view': dialog_view,
            'close_dialog': close_dialog_with_ai,
            **kwargs
        }
        return self._execute_action('ACTION_TEST', **params)


class SetTextFunction(BaseSandboxFunction):
    """设置文本函数"""

    def __call__(self,
                 pkg: str,
                 id: str,
                 content: str,
                 input_type: Optional[str] = None,
                 dialog_view: Optional[Union[List[str], str]] = None,
                 close_dialog_with_ai: bool = False,
                 **kwargs) -> CommandResult:
        """
        设置文本

        Args:
            id: 元素ID
            xpath: XPath选择器
            text: 要设置的文本
            pkg: 包名
            close_dialog: 是否关闭对话框
            **kwargs: 其他参数

        Returns:
            CommandResult: 执行结果
        """
        params = {
            'pkg': pkg,
            'id': id,
            'input_type': input_type,
            'dialog_view': dialog_view,
            'close_dialog': close_dialog_with_ai,
            **kwargs
        }
        return self._execute_action('ACTION_SET_TEXT', anonymous_param=content, **params)


class OpenHomeFunction(BaseSandboxFunction):
    """打开主页函数"""

    def __call__(self,
                 pkg: str = None,
                 reset: bool = False,
                 close_dialog_with_ai: bool = False,
                 **kwargs) -> CommandResult:
        """
        打开应用主页

        Args:
            pkg: 包名
            reset: 是否重置
            close_dialog_with_ai: 是否关闭对话框
            **kwargs: 其他参数

        Returns:
            CommandResult: 执行结果
        """
        params = {
            'pkg': pkg,
            'reset': reset,
            'close_dialog': close_dialog_with_ai,
            **kwargs
        }
        return self._execute_action('ACTION_OPEN_HOME', **params)


class CollectItemsFunction(BaseSandboxFunction):
    """收集项目信息函数"""

    def __call__(self,
                 pkg: str,
                 id: str,
                 fields: Dict[str, str],
                 important_fields: Optional[Union[List[str], str]] = None,
                 ignore_fields: Optional[Union[List[str], str]] = None,
                 size: Optional[int] = None,
                 scroll: Optional[bool] = False,
                 reverse: Optional[bool] = False,
                 singleton: Optional[bool] = None,
                 loading_view: Optional[str] = None,
                 dialog_view: Optional[Union[List[str], str]] = None,
                 close_dialog_with_ai: bool = False,
                 **kwargs) -> CommandResult:
        """
        收集项目信息

        Args:
        pkg: 包名
            id: 容器元素ID
            fields: 字段定义
            size: 收集数量
            scroll: 是否滚动
            reverse: 是否反向
            close_dialog_with_ai: 是否关闭对话框
            **kwargs: 其他参数

        Returns:
            CommandResult: 执行结果
        """
        fields_part = ','.join([f'{k}={v}' for k, v in fields.items()])
        important_fields_part = ','.join(important_fields) if isinstance(important_fields, list) else important_fields
        ignore_fields_part = ','.join(ignore_fields) if isinstance(ignore_fields, list) else ignore_fields

        params = {
            'pkg': pkg,
            'id': id,
            'important_fields': important_fields_part,
            'ignore_fields': ignore_fields_part,
            'size': size,
            'scroll': scroll,
            'reverse': reverse,
            'singleton': singleton,
            'loading_view': loading_view,
            'dialog_view': dialog_view,
            'close_dialog': close_dialog_with_ai,
            **kwargs
        }
        return self._execute_action('ACTION_COLLECT_ITEM_INFO', anonymous_param=fields_part, **params)


def create_sandbox_functions(command_executor) -> Dict[str, Any]:
    """
    创建沙盒函数字典

    Args:
        command_executor: 命令执行器

    Returns:
        Dict[str, Any]: 函数字典
    """
    return {
        'click': ClickFunction(command_executor),
        'test': TestFunction(command_executor),
        'set_text': SetTextFunction(command_executor),
        'open_home': OpenHomeFunction(command_executor),
        'collect_items': CollectItemsFunction(command_executor)
    }