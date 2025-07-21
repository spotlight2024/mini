#!/usr/bin/env python3
"""
测试 get_visible_page 性能优化效果
"""

import time
import asyncio
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.api.models import ConnectRequest
from hybrid_driver.api.routers.device import connect
from hybrid_driver.utils.async_utils import run_sync
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)


async def test_visible_page_performance():
    """测试可见页面获取性能"""
    
    # 连接设备
    serial_id = "47.94.130.125:6521"
    await connect(ConnectRequest(serial_id=serial_id))
    
    # 获取设备
    device = await run_sync(DevicePool().get, serial_id)
    if device is None:
        logger.error("设备未找到")
        return
    
    # 获取WebDriver
    driver = device.web_executor.get_raw_remote_webdriver()
    if driver is None:
        logger.error("WebDriver未初始化")
        return
    
    logger.info("开始性能测试...")
    
    # 测试超快速方法
    try:
        logger.info("=== 测试超快速方法 ===")
        start_time = time.time()
        result1 = WebDriverUtils.get_visible_page_ultra_fast(driver)
        end_time = time.time()
        ultra_fast_time = (end_time - start_time) * 1000
        logger.info(f"超快速方法执行时间: {ultra_fast_time:.2f}ms")
        logger.info(f"结果: {result1}")
    except Exception as e:
        logger.error(f"超快速方法测试失败: {e}")
        ultra_fast_time = None
    
    # 测试JavaScript注入方法
    try:
        logger.info("=== 测试JavaScript注入方法 ===")
        start_time = time.time()
        result2 = WebDriverUtils.get_visible_page_js_injection(driver)
        end_time = time.time()
        js_injection_time = (end_time - start_time) * 1000
        logger.info(f"JavaScript注入方法执行时间: {js_injection_time:.2f}ms")
        logger.info(f"结果: {result2}")
    except Exception as e:
        logger.error(f"JavaScript注入方法测试失败: {e}")
        js_injection_time = None
    
    # 测试快速方法
    try:
        logger.info("=== 测试快速方法 ===")
        start_time = time.time()
        result3 = WebDriverUtils.get_visible_page_fast(driver)
        end_time = time.time()
        fast_time = (end_time - start_time) * 1000
        logger.info(f"快速方法执行时间: {fast_time:.2f}ms")
        logger.info(f"结果: {result3}")
    except Exception as e:
        logger.error(f"快速方法测试失败: {e}")
        fast_time = None
    
    # 测试优化方法
    try:
        logger.info("=== 测试优化方法 ===")
        start_time = time.time()
        result4 = WebDriverUtils.get_visible_page(driver)
        end_time = time.time()
        optimized_time = (end_time - start_time) * 1000
        logger.info(f"优化方法执行时间: {optimized_time:.2f}ms")
        logger.info(f"结果: {result4}")
    except Exception as e:
        logger.error(f"优化方法测试失败: {e}")
        optimized_time = None
    
    # 测试集成方法（selenium_executor中的方法）
    try:
        logger.info("=== 测试集成方法 ===")
        start_time = time.time()
        result5 = await run_sync(device.web_executor.get_visible_pages)
        end_time = time.time()
        integrated_time = (end_time - start_time) * 1000
        logger.info(f"集成方法执行时间: {integrated_time:.2f}ms")
        logger.info(f"结果: {result5}")
    except Exception as e:
        logger.error(f"集成方法测试失败: {e}")
        integrated_time = None
    
    # 性能对比
    logger.info("=== 性能对比 ===")
    times = []
    methods = []
    
    if ultra_fast_time:
        times.append(ultra_fast_time)
        methods.append("超快速方法")
    
    if js_injection_time:
        times.append(js_injection_time)
        methods.append("JavaScript注入方法")
    
    if fast_time:
        times.append(fast_time)
        methods.append("快速方法")
    
    if optimized_time:
        times.append(optimized_time)
        methods.append("优化方法")
    
    if integrated_time:
        times.append(integrated_time)
        methods.append("集成方法")
    
    if times:
        min_time = min(times)
        min_method = methods[times.index(min_time)]
        max_time = max(times)
        max_method = methods[times.index(max_time)]
        
        logger.info(f"最快方法: {min_method} ({min_time:.2f}ms)")
        logger.info(f"最慢方法: {max_method} ({max_time:.2f}ms)")
        
        if max_time > 0:
            improvement = ((max_time - min_time) / max_time) * 100
            logger.info(f"性能提升: {improvement:.1f}%")
    
    # 测试缓存效果
    logger.info("=== 测试缓存效果 ===")
    cache_times = []
    for i in range(5):
        start_time = time.time()
        result = WebDriverUtils.get_visible_page(driver)
        end_time = time.time()
        cache_time = (end_time - start_time) * 1000
        cache_times.append(cache_time)
        logger.info(f"第{i+1}次调用: {cache_time:.2f}ms")
    
    avg_cache_time = sum(cache_times) / len(cache_times)
    logger.info(f"缓存后平均执行时间: {avg_cache_time:.2f}ms")
    
    if times:
        best_time = min(times)
        cache_improvement = ((best_time - avg_cache_time) / best_time) * 100
        logger.info(f"缓存优化效果: {cache_improvement:.1f}%")
    
    # 测试超快速方法的缓存效果
    logger.info("=== 测试超快速方法缓存效果 ===")
    ultra_cache_times = []
    for i in range(5):
        start_time = time.time()
        result = WebDriverUtils.get_visible_page_ultra_fast(driver)
        end_time = time.time()
        cache_time = (end_time - start_time) * 1000
        ultra_cache_times.append(cache_time)
        logger.info(f"超快速方法第{i+1}次调用: {cache_time:.2f}ms")
    
    avg_ultra_cache_time = sum(ultra_cache_times) / len(ultra_cache_times)
    logger.info(f"超快速方法缓存后平均执行时间: {avg_ultra_cache_time:.2f}ms")
    
    logger.info("性能测试完成")


if __name__ == "__main__":
    asyncio.run(test_visible_page_performance()) 