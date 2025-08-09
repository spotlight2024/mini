"""脚本执行器主入口文件"""

from fastapi import APIRouter, Request

# 导入重构后的组件
from .models.script_models import ScriptExecuteRequest, CommandResult
from .services.script_service import ScriptExecutionService
from .exceptions.executor_exceptions import ScriptExecutionException

commandRouter = APIRouter(
    prefix="/script",
    tags=["Android原生指令执行"]
)

# 创建脚本执行服务实例
script_service = ScriptExecutionService()

@commandRouter.post("/execute", response_model=CommandResult)
async def execute(http_request: Request, request_data: ScriptExecuteRequest) -> CommandResult:
    """执行脚本"""
    try:
        # 使用重构后的服务执行脚本，传递正确的参数
        result = await script_service.execute_script(
            req_id=request_data.req_id,
            ip=request_data.ip,
            port=request_data.port,
            script=request_data.script
        )
        return result

    except ScriptExecutionException as e:
        print(f"[ERROR] Script execution failed: {e.message}")
        return e.result
    except Exception as e:
        import traceback
        error_msg = f"Script execution failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        return CommandResult(
            code=1,
            message=error_msg
        )
