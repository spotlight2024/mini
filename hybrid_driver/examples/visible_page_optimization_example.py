#!/usr/bin/env python3
"""
可见页面获取优化使用示例
"""

import asyncio
import time
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.api.models import ConnectRequest
from hybrid_driver.api.routers.device import connect
from hybrid_driver.utils.async_utils import run_sync
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)


async def example_ultra_fast_method():
    """示例：使用超快速方法获取可见页面"""
    logger.info("=== 示例：超快速方法 ===")
    
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
    
    # 使用超快速方法
    start_time = time.time()
    visible_page = WebDriverUtils.get_visible_page_ultra_fast(driver)
    end_time = time.time()
    
    execution_time = (end_time - start_time) * 1000
    logger.info(f"超快速方法执行时间: {execution_time:.2f}ms")
    logger.info(f"可见页面: {visible_page}")
    
    return visible_page


async def example_js_injection_method():
    """示例：使用JavaScript注入方法获取可见页面"""
    logger.info("=== 示例：JavaScript注入方法 ===")
    
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
    
    # 使用JavaScript注入方法
    start_time = time.time()
    visible_page = WebDriverUtils.get_visible_page_js_injection(driver)
    end_time = time.time()
    
    execution_time = (end_time - start_time) * 1000
    logger.info(f"JavaScript注入方法执行时间: {execution_time:.2f}ms")
    logger.info(f"可见页面: {visible_page}")
    
    return visible_page


async def example_integrated_method():
    """示例：使用集成方法（自动选择最优方法）"""
    logger.info("=== 示例：集成方法 ===")
    
    # 连接设备
    serial_id = "47.94.130.125:6521"
    await connect(ConnectRequest(serial_id=serial_id))
    
    # 获取设备
    device = await run_sync(DevicePool().get, serial_id)
    if device is None:
        logger.error("设备未找到")
        return
    
    # 使用集成方法（自动选择最优方法）
    start_time = time.time()
    visible_page = await run_sync(device.web_executor.get_visible_pages)
    end_time = time.time()
    
    execution_time = (end_time - start_time) * 1000
    logger.info(f"集成方法执行时间: {execution_time:.2f}ms")
    logger.info(f"可见页面: {visible_page}")
    
    return visible_page


async def example_performance_comparison():
    """示例：性能对比"""
    logger.info("=== 示例：性能对比 ===")
    
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
    
    # 测试不同方法的性能
    methods = [
        ("超快速方法", WebDriverUtils.get_visible_page_ultra_fast),
        ("JavaScript注入方法", WebDriverUtils.get_visible_page_js_injection),
        ("快速方法", WebDriverUtils.get_visible_page_fast),
        ("优化方法", WebDriverUtils.get_visible_page),
    ]
    
    results = {}
    
    for method_name, method_func in methods:
        try:
            logger.info(f"测试 {method_name}...")
            start_time = time.time()
            result = method_func(driver)
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            results[method_name] = {
                'time': execution_time,
                'result': result,
                'success': True
            }
            
            logger.info(f"{method_name}执行时间: {execution_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"{method_name}测试失败: {e}")
            results[method_name] = {
                'time': None,
                'result': None,
                'success': False,
                'error': str(e)
            }
    
    # 性能对比
    logger.info("=== 性能对比结果 ===")
    successful_results = {k: v for k, v in results.items() if v['success'] and v['time'] is not None}
    
    if successful_results:
        times = [(name, data['time']) for name, data in successful_results.items()]
        times.sort(key=lambda x: x[1])  # 按时间排序
        
        logger.info("性能排名:")
        for i, (name, time_ms) in enumerate(times, 1):
            logger.info(f"{i}. {name}: {time_ms:.2f}ms")
        
        if len(times) > 1:
            fastest = times[0]
            slowest = times[-1]
            improvement = ((slowest[1] - fastest[1]) / slowest[1]) * 100
            logger.info(f"最快方法 {fastest[0]} 比最慢方法 {slowest[0]} 快 {improvement:.1f}%")
    
    return results


async def example_cache_effect():
    """示例：缓存效果测试"""
    logger.info("=== 示例：缓存效果测试 ===")
    
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
    
    # 测试缓存效果
    logger.info("测试超快速方法的缓存效果...")
    cache_times = []
    
    for i in range(5):
        start_time = time.time()
        result = WebDriverUtils.get_visible_page_ultra_fast(driver)
        end_time = time.time()
        cache_time = (end_time - start_time) * 1000
        cache_times.append(cache_time)
        logger.info(f"第{i+1}次调用: {cache_time:.2f}ms")
    
    avg_cache_time = sum(cache_times) / len(cache_times)
    min_cache_time = min(cache_times)
    max_cache_time = max(cache_times)
    
    logger.info(f"缓存效果统计:")
    logger.info(f"  平均时间: {avg_cache_time:.2f}ms")
    logger.info(f"  最快时间: {min_cache_time:.2f}ms")
    logger.info(f"  最慢时间: {max_cache_time:.2f}ms")
    logger.info(f"  时间差异: {max_cache_time - min_cache_time:.2f}ms")
    
    return cache_times


async def main():
    """主函数"""
    logger.info("开始可见页面获取优化示例...")
    
    try:
        # 示例1: 超快速方法
        await example_ultra_fast_method()
        
        # 示例2: JavaScript注入方法
        await example_js_injection_method()
        
        # 示例3: 集成方法
        await example_integrated_method()
        
        # 示例4: 性能对比
        await example_performance_comparison()
        
        # 示例5: 缓存效果
        await example_cache_effect()
        
        logger.info("所有示例执行完成")
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 