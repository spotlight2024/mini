from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins
from RestrictedPython.PrintCollector import PrintCollector
import asyncio
import aiohttp
import json
import threading
import re

class EncoderUtils:
    """编码工具类，用于对参数值进行编码以避免特殊字符问题"""
    
    # 需要转义的特殊字符集合
    HEX_CHARS = {' ', '\n', '\r', '\t', '#', '=', ',', '|', '-', '[', ']', '{', '}'}
    
    @staticmethod
    def encode_string(text: str) -> str:
        """
        将字符串中的特殊字符进行十六进制编码
        
        Args:
            text: 需要编码的字符串
            
        Returns:
            编码后的字符串
        """
        if not text:
            return text
            
        result = []
        for char in text:
            if char in EncoderUtils.HEX_CHARS:
                # 将特殊字符转换为 %XX 格式
                result.append(f'%{ord(char):02X}')
            else:
                result.append(char)
        
        return ''.join(result)

class Script(BaseModel):
    id: str
    name: str
    commands: str
    params: Optional[dict[str, str]] = None
    cancellable: bool
    version: int

class ScriptExecuteRequest(BaseModel):
    req_id: str
    port: int
    script: Script

class CommandExecuteRequest(BaseModel):
    req_id: str
    command: str

class CommandResult(BaseModel):
    code: int
    data: Optional[str] = None
    message: Optional[str] = None

class ExecutorContext:
    def __init__(self):
        self.params: dict[str, str] = {}
        self.results: list[CommandResult] = []

class ExecutorException(BaseException):
    result: CommandResult

    def __init__(self, result: CommandResult):
        self.result = result

class CommandExecutor:
    req_id: str = "0"
    command_execute_url: str = ""
    commands: str = ""

    def __init__(self, req_id: str, command_execute_url: str, params: dict[str, str], commands: str):
        self.req_id = req_id
        self.command_execute_url = command_execute_url
        self.context = ExecutorContext()  # 为每个实例创建独立的context
        self.context.params = params
        self.commands = commands

    def _replace_variables(self, commands: str) -> str:
        """
        替换commands中的变量占位符
        
        Args:
            commands: 包含{{PARAM_NAME}}格式占位符的命令字符串
            
        Returns:
            替换变量后的命令字符串
        """
        def replace_variable(match):
            param_name = match.group(1)  # 获取{{}}中的参数名
            if param_name in self.context.params:
                # 获取参数值并进行编码
                param_value = self.context.params[param_name]
                encoded_value = EncoderUtils.encode_string(param_value)
                print(f"[VARIABLE_REPLACE] {param_name} = '{param_value}' -> '{encoded_value}'")
                return encoded_value
            else:
                print(f"[VARIABLE_REPLACE] Warning: Parameter '{param_name}' not found in params")
                return match.group(0)  # 如果找不到参数，保持原样
        
        # 使用正则表达式查找并替换所有{{PARAM_NAME}}格式的占位符
        pattern = r'\{\{([^}]+)\}\}'
        result = re.sub(pattern, replace_variable, commands)
        
        if result != commands:
            print(f"[VARIABLE_REPLACE] Original: {commands}")
            print(f"[VARIABLE_REPLACE] Replaced: {result}")
        
        return result

    async def execute(self):
        # 在执行前先替换变量
        processed_commands = self._replace_variables(self.commands)
        result = await self._execute_sandboxed(processed_commands)
        return result

    async def _execute_sandboxed(self, code: str) -> str:
        """异步执行沙盒代码"""
        print(f"[SANDBOX] Executing commands: {code}")

        # 为沙盒创建一个异步执行环境
        class AsyncExecuteCommandWrapper:
            def __init__(self, executor):
                self.executor = executor

            def __call__(self, command: str):
                """同步接口，内部处理异步调用"""
                result_container = {}

                async def _async_call():
                    try:
                        result: CommandResult = await self.executor.execute_command(command)
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

                command_execute_result: CommandResult
                if 'exception' in result_container:
                    command_execute_result = CommandResult(code=1, message=str(result_container['exception']))
                else:
                    command_execute_result = result_container.get('result', CommandResult(code=1, message="Unknown error"))

                self.executor.context.results.append(command_execute_result)
                if command_execute_result.code != 0:
                    raise ExecutorException(command_execute_result)
                else:
                    return command_execute_result

        # 自定义迭代器解包函数 - 修复参数签名
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

        try:
            byte_code = compile_restricted(code, '<string>', 'exec')

            # 创建沙盒环境
            env = {
                '__builtins__': safe_builtins,
                '_print_': PrintCollector,  # 使用类，不是实例
                '_getiter_': iter,
                '_getitem_': safe_getitem,
                '_getattr_': safe_getattr,
                '_setattr_': setattr,
                '_iter_unpack_sequence_': safe_iter_unpack_sequence,
                'execute_command': AsyncExecuteCommandWrapper(self),
                'params': self.context.params,
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

            # 执行代码
            exec(byte_code, env)

            # 获取打印输出
            if '_print' in env and hasattr(env['_print'], 'txt'):
                output_text = env['_print'].txt
            else:
                output_text = "No output captured"

            print(f"[SANDBOX] Executed commands output: {output_text}")
            return output_text
        except Exception as e:
            error_msg = f"Sandbox error: {e}"
            print(f"[SANDBOX ERROR] {error_msg}")
            self.context.results.append(CommandResult(code=1, message=error_msg))
            import traceback
            traceback.print_exc()
            return error_msg

    async def execute_command(self, command: str) -> CommandResult:
        """异步执行指令，通过HTTP请求发送到客户端"""
        request_data = CommandExecuteRequest(req_id=self.req_id, command=command)

        # 打印HTTP请求信息
        print(f"[HTTP REQUEST] URL: {self.command_execute_url}")
        print(f"[HTTP REQUEST] Method: POST")
        print(f"[HTTP REQUEST] Headers: Content-Type: application/json")
        print(f"[HTTP REQUEST] Body: {json.dumps(request_data.dict(), ensure_ascii=False, indent=2)}")
        print("-" * 50)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.command_execute_url,
                    json=request_data.dict(),
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    # 打印HTTP响应状态
                    print(f"[HTTP RESPONSE] Status: {response.status}")
                    print(f"[HTTP RESPONSE] Headers: {dict(response.headers)}")

                    if response.status == 200:
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
                                return error_result
                            # 反序列化为 CommandResult 对象
                            command_result = CommandResult(**result_data)
                            print(f"[SUCCESS] Command executed successfully: {command_result}")
                            return command_result
                        except json.JSONDecodeError as e:
                            error_result = CommandResult(
                                code=1,
                                message=f"Failed to parse JSON response: {str(e)}"
                            )
                            print(f"[ERROR] JSON Parse Error: {error_result.message}")
                            print("=" * 50)
                            return error_result
                        except TypeError as e:
                            error_result = CommandResult(
                                code=1,
                                message=f"Invalid response data format: {str(e)}"
                            )
                            print(f"[ERROR] Type Error: {error_result.message}")
                            print("=" * 50)
                            return error_result
                    else:
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
                        return error_result
        except asyncio.TimeoutError:
            error_result = CommandResult(code=1, message="Request timeout")
            print(f"[ERROR] Timeout: {error_result.message}")
            print("=" * 50)
            return error_result
        except aiohttp.ClientError as e:
            error_result = CommandResult(code=1, message=f"HTTP client error: {str(e)}")
            print(f"[ERROR] Client Error: {error_result.message}")
            print("=" * 50)
            return error_result
        except Exception as e:
            error_result = CommandResult(code=1, message=f"Request failed: {str(e)}")
            print(f"[ERROR] General Error: {error_result.message}")
            print("=" * 50)
            return error_result

commandRouter = APIRouter(
    prefix="/script",
    tags=["Android原生指令执行"]
)

def _build_script_result(executor: CommandExecutor) -> CommandResult:
    # 如果没有结果，直接返回失败
    if not executor.context.results:
        return CommandResult(code=1, message="Task has no op")

    # 如果只有一个结果，直接返回该结果
    if len(executor.context.results) == 1:
        return executor.context.results[0]

    last_result = executor.context.results[-1]
    # 如果最后一个结果失败，直接返回最后一个结果
    if last_result.code != 0:
        return last_result

    # 多个结果需要合并
    merged_data = {}
    for result in executor.context.results:
        if result.data:
            try:
                # 尝试解析 JSON 数据
                if isinstance(result.data, str):
                    item_data = json.loads(result.data)
                else:
                    item_data = result.data

                # 合并 JSON 对象
                if isinstance(item_data, dict):
                    merged_data.update(item_data)
                else:
                    # 如果不是字典，使用索引作为键
                    merged_data[f"result_{len(merged_data)}"] = item_data
            except (json.JSONDecodeError, TypeError) as e:
                print(f"[WARNING] Failed to merge result data: {e}")
                # 如果解析失败，直接使用原始数据
                merged_data[f"result_{len(merged_data)}"] = result.data
    return CommandResult(code=0, data=json.dumps(merged_data, ensure_ascii=False), message="success")

@commandRouter.post("/execute", response_model=CommandResult)
async def execute(httpRequest: Request, requestData: ScriptExecuteRequest) -> CommandResult:
    print(f"[REQUEST] data: {requestData}")
    req_id = requestData.req_id
    client_ip = httpRequest.client.host if httpRequest.client else "unknown"
    command_execute_url = f"http://127.0.0.1:{requestData.port}/execute"
    params = requestData.script.params
    if params == None:
        params = {}

    executor = CommandExecutor(
        req_id=req_id,
        command_execute_url=command_execute_url,
        params=params,
        commands=requestData.script.commands,
    )
    try:
        await executor.execute()

        final_result = _build_script_result(executor)
        return final_result
    except ExecutorException as e:
        print(f"[ERROR] Request {req_id} failed: {e}")
        return e.result
    except Exception as e:
        print(f"[ERROR] Request {req_id} failed: {e}")
        return CommandResult(code=1, message=f"execute failed: {e}")
