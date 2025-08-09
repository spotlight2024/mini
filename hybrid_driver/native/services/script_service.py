"""脚本执行服务"""

from typing import Dict, List, Tuple, Optional
import sys
import os

# 添加父目录到路径以支持绝对导入
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ..models.script_models import Script, CommandResult, ExecutorContext
from .network_service import NetworkService
from ..utils.variable_replacer import VariableReplacer
from ..utils.result_merger import ResultMerger
from ..executors.http_executor import HttpCommandExecutor
from ..executors.sandbox_executor import SandboxScriptExecutor
from ..exceptions.executor_exceptions import ScriptExecutionException, NetworkException


class ScriptExecutionService:
    """脚本执行服务，协调各个组件完成脚本执行"""

    def __init__(
        self,
        network_service: Optional[NetworkService] = None,
        variable_replacer: Optional[VariableReplacer] = None,
        result_merger: Optional[ResultMerger] = None
    ):
        """
        初始化脚本执行服务

        Args:
            network_service: 网络服务
            variable_replacer: 变量替换器
            result_merger: 结果合并器
        """
        self.network_service = network_service or NetworkService()
        self.variable_replacer = variable_replacer
        self.result_merger = result_merger or ResultMerger()

    async def execute_script(
        self,
        req_id: str,
        ip: str,
        port: int,
        script: Script,
        timeout: int = 120
    ) -> CommandResult:
        """
        执行脚本

        Args:
            req_id: 请求ID
            ip: 目标IP地址
            port: 目标端口
            script: 要执行的脚本
            timeout: 超时时间

        Returns:
            CommandResult: 执行结果

        Raises:
            ScriptExecutionException: 当脚本执行失败时
        """
        try:
            # 1. 解析目标IP
            resolved_ip = self.network_service.resolve_target_ip(ip)
            command_execute_url = f"http://{resolved_ip}:{port}/execute"

            # 2. 准备参数和变量替换器
            params = script.params or {}
            variable_replacer = VariableReplacer(params)

            # 3. 替换脚本中的变量
            processed_commands = variable_replacer.replace_variables(script.commands)

            # 4. 创建执行器上下文
            context = ExecutorContext(params=params)

            # 5. 创建HTTP命令执行器
            http_executor = HttpCommandExecutor(
                req_id=req_id,
                command_execute_url=command_execute_url,
                context=context,
                timeout=timeout
            )

            # 6. 创建沙盒脚本执行器
            sandbox_executor = SandboxScriptExecutor(
                command_executor=http_executor,
                context=context
            )

            # 7. 执行脚本
            await sandbox_executor.execute_script(processed_commands)

            # 8. 构建最终结果
            final_result = self._build_script_result(sandbox_executor)
            return final_result

        except ScriptExecutionException as e:
            print(f"[ERROR] Script execution failed for request {req_id}: {e}")
            return e.result
        except Exception as e:
            error_msg = f"Script execution failed: {e}"
            print(f"[ERROR] Request {req_id} failed: {error_msg}")
            error_result = CommandResult(code=1, message=error_msg)
            raise ScriptExecutionException(error_msg, error_result) from e

    def _build_script_result(self, executor: SandboxScriptExecutor) -> CommandResult:
        """
        构建脚本执行结果

        Args:
            executor: 脚本执行器

        Returns:
            CommandResult: 最终结果
        """
        results = executor.get_context().results

        # 如果没有结果，直接返回失败
        if not results:
            return CommandResult(code=1, message="Task has no operations")

        # 使用结果合并器合并结果
        return self.result_merger.merge_results(results)

    def validate_script(self, script: Script) -> tuple[bool, list[str]]:
        """
        验证脚本的有效性

        Args:
            script: 要验证的脚本

        Returns:
            tuple[bool, list[str]]: (是否有效, 错误消息列表)
        """
        errors = []

        # 检查脚本基本信息
        if not script.id:
            errors.append("Script ID is required")

        if not script.name:
            errors.append("Script name is required")

        if not script.commands:
            errors.append("Script commands are required")

        # 检查变量
        if script.commands:
            params = script.params or {}
            variable_replacer = VariableReplacer(params)
            is_valid, missing_vars = variable_replacer.validate_variables(script.commands)

            if not is_valid:
                errors.append(f"Missing parameters: {', '.join(missing_vars)}")

        return len(errors) == 0, errors

    def get_script_variables(self, script: Script) -> list[str]:
        """
        获取脚本中的所有变量

        Args:
            script: 脚本对象

        Returns:
            list[str]: 变量名列表
        """
        if not script.commands:
            return []

        variable_replacer = VariableReplacer()
        return variable_replacer.find_variables(script.commands)

    def create_execution_context(self, params: Optional[Dict[str, str]] = None) -> ExecutorContext:
        """
        创建执行上下文

        Args:
            params: 参数字典

        Returns:
            ExecutorContext: 执行上下文
        """
        return ExecutorContext(params=params or {})

    def set_network_service(self, network_service: NetworkService) -> None:
        """
        设置网络服务

        Args:
            network_service: 网络服务实例
        """
        self.network_service = network_service

    def set_result_merger(self, result_merger: ResultMerger) -> None:
        """
        设置结果合并器

        Args:
            result_merger: 结果合并器实例
        """
        self.result_merger = result_merger