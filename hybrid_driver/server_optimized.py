import asyncio
import json
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from hybrid_driver.api.models import APIResponse

# 导入路由模块
from hybrid_driver.api.routers import collect, device, element, mock, page, screenshot, restaurant
from hybrid_driver.api.test import taobao_test_api
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.log_config import get_logger
from hybrid_driver.native import script_executor
from hybrid_driver.operation import OperationItem, OperationSequence
from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor

# 创建FastAPI应用
app = FastAPI(
    title="SpotLight Hybrid Driver API",
    description="混合驱动自动化测试API服务",
    version="1.0.0",
)

# 初始化全局组件
device_pool = DevicePool()

logger = get_logger(__name__)

# 注册路由
app.include_router(device.router)
app.include_router(element.router)
app.include_router(page.router)
app.include_router(collect.router)
app.include_router(mock.router)
app.include_router(screenshot.router)
app.include_router(restaurant.router)
app.include_router(taobao_test_api.router)

app.include_router(script_executor.commandRouter)

# 挂载静态文件服务 - 用于提供截图文件访问
import os
screenshot_dir = "/app/@web_screenshot"
if os.path.exists(screenshot_dir):
    app.mount("/@web_screenshot", StaticFiles(directory=screenshot_dir, html=True), name="screenshots")

@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "SpotLight Hybrid Driver API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ========== 轻量 trace_id 中间件与统一异常处理 ==========
@app.middleware("http")
async def inject_trace_id(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or str(int(time.time() * 1000))
    request.state.trace_id = trace_id
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception(f"Unhandled exception: {exc}")
        payload = APIResponse(
            code=2000,
            message="系统异常",
            error=str(exc),
            trace_id=trace_id,
        ).model_dump()
        response = JSONResponse(status_code=500, content=payload)
    response.headers["X-Trace-Id"] = trace_id
    return response




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10001)
