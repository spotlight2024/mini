#!/usr/bin/env python3
"""
简单性能测试脚本 - 测试新的最简单可见页面获取方法
"""

import time
import asyncio
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.api.models import ConnectConfig
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)

async def test_simple_method():
    """测试最简单方法"""
    logger.info("🚀 开始测试最简单方法")
    
    # 连接设备
    config = ConnectConfig(
        serial_id="47.94.130.125:6521",
        user_id="0",
        android_process="com.tencent.mm:appbrand0"
    )
    
    device = DevicePool().connect(config)
    driver = device._web_execute._driver
    
    try:
        # 测试最简单方法
        logger.info("📋 测试 get_visible_page_simple")
        start_time = time.time()
        result = WebDriverUtils.get_visible_page_simple(driver, 2)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        logger.info(f"✅ 最简单方法结果: {result}")
        logger.info(f"⏱️ 最简单方法耗时: {execution_time_ms:.2f}ms")
        
        # 测试快速方法
        logger.info("📋 测试 get_visible_page_fast")
        start_time = time.time()
        result = WebDriverUtils.get_visible_page_fast(driver, 3)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        logger.info(f"✅ 快速方法结果: {result}")
        logger.info(f"⏱️ 快速方法耗时: {execution_time_ms:.2f}ms")
        
        # 测试超快速方法
        logger.info("📋 测试 get_visible_page_ultra_fast")
        start_time = time.time()
        result = WebDriverUtils.get_visible_page_ultra_fast(driver, 1)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        logger.info(f"✅ 超快速方法结果: {result}")
        logger.info(f"⏱️ 超快速方法耗时: {execution_time_ms:.2f}ms")
        
        # 测试标准方法
        logger.info("📋 测试 get_visible_page")
        start_time = time.time()
        result = WebDriverUtils.get_visible_page(driver, 10)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        logger.info(f"✅ 标准方法结果: {result}")
        logger.info(f"⏱️ 标准方法耗时: {execution_time_ms:.2f}ms")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
    finally:
        driver.quit()

def main():
    """主函数"""
    logger.info("🎯 开始性能测试")
    asyncio.run(test_simple_method())
    logger.info("🏁 性能测试完成")

if __name__ == "__main__":
    main() 