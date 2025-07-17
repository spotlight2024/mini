import time
import asyncio
from fastapi import FastAPI

from hybrid_driver.device_pool import DevicePool
from hybrid_driver.auto_scaler import SpotLightAutoScaler
from hybrid_driver.log_config import get_logger

# 导入路由模块
from hybrid_driver.api.routers import device, element, page, collect, mock
from hybrid_driver.operation import OperationItem, OperationSequence
from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor

# 创建FastAPI应用
app = FastAPI(
    title="SpotLight Hybrid Driver API",
    description="混合驱动自动化测试API服务",
    version="1.0.0"
)

# 初始化全局组件
device_pool = DevicePool()
auto_scaler = SpotLightAutoScaler()
auto_scaler.start_monitoring()

logger = get_logger(__name__)

# 注册路由
app.include_router(device.router)
app.include_router(element.router)
app.include_router(page.router)
app.include_router(collect.router)
app.include_router(mock.router)


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
        "docs": "/docs"
    }


if __name__ == "__main__":
    async def main():
        """主函数 - 用于测试"""
        serial_id = "123.56.152.41:6529"

        # 等待连接操作完成
        from hybrid_driver.api.models import ConnectRequest
        from hybrid_driver.api.routers.device import connect

        await connect(ConnectRequest(serial_id=serial_id, user_id="10"))

        # switch to current page
        device = await asyncio.get_event_loop().run_in_executor(
            None, device_pool.get, serial_id
        )
        if device is None:
            logger.error("设备未找到")
            return

        # 获取可见页面并切换
        executor: SeleniumWebExecutor = device.web_executor
        driver = executor.get_raw_remote_webdriver()
        if driver is None:
            logger.error("WebExecutor未初始化")
            return
        pages = await asyncio.get_event_loop().run_in_executor(
            None, device.web_executor.get_visible_pages
        )

        logger.info(f"pages : ${pages}")

        operations = [
            # 查找搜索按钮
            OperationItem("click", method="css selector", selector="wx-view.marketingPopup-index--button-close", timeout=2),
            OperationItem("click", method="css selector", selector="wx-view.search-box.searchBox--search-box",timeout=2),

        ]

        sequence = OperationSequence(operations)
        results = sequence.execute(device)

        for i, result in enumerate(results):
            print(f"Step {i + 1}: {'Success' if result['success'] else 'Failed'}")
            if not result['success']:
                print(f"Error: {result['error']}")
            print(f"Time: {result['elapsed']:.2f}s")

        device.disconnect()


    # 运行异步主函数
    asyncio.run(main())
