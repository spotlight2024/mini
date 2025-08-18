"""沙盒脚本执行器"""

import asyncio
import threading
from typing import Optional, Dict, Any
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins
from RestrictedPython.PrintCollector import PrintCollector

from .base_executor import ScriptExecutorInterface, CommandExecutorInterface
from ..models.script_models import CommandResult, ExecutorContext
from ..exceptions.executor_exceptions import SandboxException, ExecutorException
from .sandbox_functions import create_sandbox_functions


class SandboxScriptExecutor(ScriptExecutorInterface):
    """沙盒脚本执行器，在受限环境中执行Python脚本"""

    def __init__(
        self,
        command_executor: CommandExecutorInterface,
        context: Optional[ExecutorContext] = None
    ):
        """
        初始化沙盒脚本执行器

        Args:
            command_executor: 命令执行器
            context: 执行器上下文
        """
        super().__init__(context)
        self.command_executor = command_executor

    async def execute(self, commands: str) -> str:
        """
        执行脚本

        Args:
            commands: 脚本命令

        Returns:
            str: 执行结果
        """
        return await self.execute_script(commands)

    async def execute_script(self, commands: str) -> str:
        """
        在沙盒环境中异步执行脚本

        Args:
            commands: 脚本代码

        Returns:
            str: 执行结果

        Raises:
            SandboxException: 当沙盒执行失败时
        """
        print(f"[SANDBOX] Executing commands: {commands}")

        try:
            # 编译受限代码
            byte_code = compile_restricted(commands, '<string>', 'exec')
            if byte_code is None:
                raise SandboxException("Failed to compile restricted code")

            # 创建沙盒环境
            env = self._create_sandbox_environment()

            # 执行代码
            exec(byte_code, env)

            # 获取打印输出
            output_text = self._extract_output(env)

            print(f"[SANDBOX] Executed commands output: {output_text}")
            return output_text

        except ExecutorException:
            # 重新抛出执行器异常
            raise
        except Exception as e:
            error_msg = f"Sandbox error: {e}"
            print(f"[SANDBOX ERROR] {error_msg}")
            self.add_result(CommandResult(code=1, message=error_msg))
            import traceback
            traceback.print_exc()
            raise SandboxException(error_msg) from e

    def _create_sandbox_environment(self) -> Dict[str, Any]:
        """
        创建沙盒执行环境

        Returns:
            Dict[str, Any]: 沙盒环境字典
        """
        # 创建异步命令执行包装器
        async_wrapper = AsyncExecuteCommandWrapper(self.command_executor, self)

        # 创建函数式API
        sandbox_functions = create_sandbox_functions(async_wrapper)

        # 自定义迭代器解包函数
        def safe_iter_unpack_sequence(seq, spec, pad=None):
            """安全的序列解包函数"""
            return list(seq)

        # 安全的属性访问函数
        def safe_getattr(obj, name, default=None, getattr=getattr):
            """安全的属性访问"""
            return getattr(obj, name, default)

        # 安全的项目访问函数
        def safe_getitem(obj, key):
            """安全的项目访问"""
            return obj[key]

        # 创建沙盒环境
        env = {
            '__builtins__': safe_builtins,
            '_print_': PrintCollector,  # 使用类，不是实例
            '_getiter_': iter,
            '_getitem_': safe_getitem,
            '_getattr_': safe_getattr,
            '_setattr_': setattr,
            '_iter_unpack_sequence_': safe_iter_unpack_sequence,
            'execute_command': async_wrapper,
            'params': self.context.params,
            # 允许的内置函数
            'len': len,
            'range': range,
            'enumerate': enumerate,
            'sum': sum,
            'int': int,
            'str': str,
            'list': list,
            'dict': dict,
            'get': lambda obj, key, default=None: obj.get(key, default) if hasattr(obj, 'get') else default,
        }

        # 添加函数式API到环境中
        env.update(sandbox_functions)

        return env

    def _extract_output(self, env: Dict[str, Any]) -> str:
        """
        从执行环境中提取输出

        Args:
            env: 执行环境

        Returns:
            str: 输出文本
        """
        if '_print' in env and hasattr(env['_print'], 'txt'):
            return env['_print'].txt
        else:
            return "No output captured"


class AsyncExecuteCommandWrapper:
    """异步命令执行包装器，用于在沙盒中提供同步接口"""

    def __init__(self, command_executor: CommandExecutorInterface, script_executor: SandboxScriptExecutor):
        """
        初始化包装器

        Args:
            command_executor: 命令执行器
            script_executor: 脚本执行器
        """
        self.command_executor = command_executor
        self.script_executor = script_executor

    def __call__(self, command: str) -> CommandResult:
        """
        同步接口，内部处理异步调用

        Args:
            command: 要执行的命令

        Returns:
            CommandResult: 命令执行结果

        Raises:
            ExecutorException: 当命令执行失败时
        """
        result_container = {}

        async def _async_call():
            try:
                result: CommandResult = await self.command_executor.execute_command(command)
                result_container['result'] = result
            except Exception as e:
                print(f"[SANDBOX] Error executing command: {command}, error: {e}")
                result_container['exception'] = e

        # 在新线程中运行异步代码
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_async_call())
            finally:
                loop.close()

        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()

        # 处理执行结果
        if 'exception' in result_container:
            command_execute_result = CommandResult(
                code=1,
                message=str(result_container['exception'])
            )
        else:
            command_execute_result = result_container.get(
                'result',
                CommandResult(code=1, message="Unknown error")
            )

        # 添加结果到脚本执行器的上下文
        self.script_executor.add_result(command_execute_result)

        # 如果命令执行失败，抛出异常
        if command_execute_result.is_failure():
            raise ExecutorException("Command execution failed", command_execute_result)

        return command_execute_result