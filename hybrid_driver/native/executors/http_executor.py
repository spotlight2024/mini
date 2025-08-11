"""HTTP命令执行器"""

import json
import asyncio
import aiohttp
from typing import Optional
from .base_executor import CommandExecutorInterface
from ..models.script_models import CommandResult, CommandExecuteRequest, ExecutorContext
from ..exceptions.executor_exceptions import HttpRequestException
from ..config import Config


class HttpCommandExecutor(CommandExecutorInterface):
    """HTTP命令执行器，通过HTTP请求发送命令到客户端执行"""

    def __init__(
        self,
        req_id: str,
        command_execute_url: str,
        context: Optional[ExecutorContext] = None,
        timeout: int = 120
    ):
        """
        初始化HTTP命令执行器

        Args:
            req_id: 请求ID
            command_execute_url: 命令执行URL
            context: 执行器上下文
            timeout: 请求超时时间（秒）
        """
        super().__init__(context)
        self.req_id = req_id
        self.command_execute_url = command_execute_url
        self.timeout = timeout

    async def execute(self, command: str) -> CommandResult:
        """
        执行命令

        Args:
            command: 要执行的命令

        Returns:
            CommandResult: 执行结果
        """
        return await self.execute_command(command)

    async def execute_command(self, command: str) -> CommandResult:
        """
        异步执行指令，通过HTTP请求发送到客户端

        Args:
            command: 要执行的命令

        Returns:
            CommandResult: 命令执行结果

        Raises:
            HttpRequestException: 当HTTP请求失败时
        """
        request_data = CommandExecuteRequest(req_id=self.req_id, command=command)

        # 打印HTTP请求信息
        self._log_request(request_data)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.command_execute_url,
                    json=request_data.dict(),
                    timeout=aiohttp.ClientTimeout(total=Config.HTTP_TIMEOUT)
                ) as response:
                    return await self._handle_response(response)

        except asyncio.TimeoutError as e:
            error_result = CommandResult(code=1, message="Request timeout")
            self._log_error("Timeout", error_result.message)
            self.add_result(error_result)
            raise HttpRequestException("Request timeout", error_result) from e

        except aiohttp.ClientError as e:
            error_result = CommandResult(code=1, message=f"HTTP client error: {str(e)}")
            self._log_error("Client Error", error_result.message)
            self.add_result(error_result)
            raise HttpRequestException(f"HTTP client error: {str(e)}", error_result) from e

        except Exception as e:
            error_result = CommandResult(code=1, message=f"Request failed: {str(e)}")
            self._log_error("General Error", error_result.message)
            self.add_result(error_result)
            raise HttpRequestException(f"Request failed: {str(e)}", error_result) from e

    async def _handle_response(self, response: aiohttp.ClientResponse) -> CommandResult:
        """
        处理HTTP响应

        Args:
            response: HTTP响应对象

        Returns:
            CommandResult: 处理后的结果
        """
        # 打印HTTP响应状态
        print(f"[HTTP RESPONSE] Status: {response.status}")
        print(f"[HTTP RESPONSE] Headers: {dict(response.headers)}")

        if response.status == 200:
            return await self._handle_success_response(response)
        else:
            return await self._handle_error_response(response)

    async def _handle_success_response(self, response: aiohttp.ClientResponse) -> CommandResult:
        """
        处理成功的HTTP响应

        Args:
            response: HTTP响应对象

        Returns:
            CommandResult: 处理后的结果
        """
        try:
            # 获取 JSON 格式的响应数据
            result_data = await response.json()

            # 打印响应内容
            print(f"[HTTP RESPONSE] Body: {json.dumps(result_data, ensure_ascii=False, indent=2)}")
            print("=" * 50)

            # 验证响应数据是否包含必要字段
            if not isinstance(result_data, dict):
                error_result = CommandResult(
                    code=1,
                    message="Invalid JSON response format: expected object"
                )
                print(f"[ERROR] {error_result.message}")
                self.add_result(error_result)
                return error_result

            # 反序列化为 CommandResult 对象
            command_result = CommandResult(**result_data)
            print(f"[SUCCESS] Command executed successfully: {command_result}")
            self.add_result(command_result)
            return command_result

        except json.JSONDecodeError as e:
            error_result = CommandResult(
                code=1,
                message=f"Failed to parse JSON response: {str(e)}"
            )
            print(f"[ERROR] JSON Parse Error: {error_result.message}")
            print("=" * 50)
            self.add_result(error_result)
            return error_result

        except TypeError as e:
            error_result = CommandResult(
                code=1,
                message=f"Invalid response data format: {str(e)}"
            )
            print(f"[ERROR] Type Error: {error_result.message}")
            print("=" * 50)
            self.add_result(error_result)
            return error_result

    async def _handle_error_response(self, response: aiohttp.ClientResponse) -> CommandResult:
        """
        处理错误的HTTP响应

        Args:
            response: HTTP响应对象

        Returns:
            CommandResult: 错误结果
        """
        # 尝试获取错误响应的内容
        try:
            error_text = await response.text()
            print(f"[HTTP RESPONSE] Error Body: {error_text}")
        except:
            error_text = "Unable to read error response"
            print(f"[HTTP RESPONSE] Error Body: {error_text}")

        error_result = CommandResult(
            code=1,
            message=f"HTTP request failed with status {response.status}: {error_text}"
        )
        print(f"[ERROR] HTTP Error: {error_result.message}")
        print("=" * 50)
        self.add_result(error_result)
        return error_result

    def _log_request(self, request_data: CommandExecuteRequest) -> None:
        """
        记录HTTP请求信息

        Args:
            request_data: 请求数据
        """
        print(f"[HTTP REQUEST] URL: {self.command_execute_url}")
        print(f"[HTTP REQUEST] Method: POST")
        print(f"[HTTP REQUEST] Headers: Content-Type: application/json")
        print(f"[HTTP REQUEST] Body: {json.dumps(request_data.dict(), ensure_ascii=False, indent=2)}")
        print("-" * 50)

    def _log_error(self, error_type: str, message: str) -> None:
        """
        记录错误信息

        Args:
            error_type: 错误类型
            message: 错误消息
        """
        print(f"[ERROR] {error_type}: {message}")
        print("=" * 50)

    def set_timeout(self, timeout: int) -> None:
        """
        设置请求超时时间

        Args:
            timeout: 超时时间（秒）
        """
        self.timeout = timeout

    def get_timeout(self) -> int:
        """
        获取请求超时时间

        Returns:
            int: 超时时间（秒）
        """
        return self.timeout

    def get_request_url(self) -> str:
        """
        获取请求URL

        Returns:
            str: 请求URL
        """
        return self.command_execute_url