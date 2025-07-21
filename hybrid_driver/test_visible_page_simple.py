#!/usr/bin/env python3
"""
简单的可见页面性能测试
"""

import time
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)


def test_visible_page_methods(driver):
    """测试不同的可见页面获取方法"""
    
    logger.info("开始性能测试...")
    
    methods = [
        ("超快速方法", WebDriverUtils.get_visible_page_ultra_fast),
        ("JavaScript注入方法", WebDriverUtils.get_visible_page_js_injection),
        ("快速方法", WebDriverUtils.get_visible_page_fast),
        ("优化方法", WebDriverUtils.get_visible_page),
    ]
    
    results = {}
    
    for method_name, method_func in methods:
        try:
            logger.info(f"=== 测试 {method_name} ===")
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
            logger.info(f"结果: {result}")
            
        except Exception as e:
            logger.error(f"{method_name}测试失败: {e}")
            results[method_name] = {
                'time': None,
                'result': None,
                'success': False,
                'error': str(e)
            }
    
    # 性能对比
    logger.info("=== 性能对比 ===")
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


def test_cache_effect(driver, method_func, method_name):
    """测试缓存效果"""
    logger.info(f"=== 测试 {method_name} 缓存效果 ===")
    
    cache_times = []
    for i in range(5):
        start_time = time.time()
        result = method_func(driver)
        end_time = time.time()
        cache_time = (end_time - start_time) * 1000
        cache_times.append(cache_time)
        logger.info(f"第{i+1}次调用: {cache_time:.2f}ms")
    
    avg_cache_time = sum(cache_times) / len(cache_times)
    min_cache_time = min(cache_times)
    max_cache_time = max(cache_times)
    
    logger.info(f"{method_name}缓存效果统计:")
    logger.info(f"  平均时间: {avg_cache_time:.2f}ms")
    logger.info(f"  最快时间: {min_cache_time:.2f}ms")
    logger.info(f"  最慢时间: {max_cache_time:.2f}ms")
    logger.info(f"  时间差异: {max_cache_time - min_cache_time:.2f}ms")
    
    return cache_times


if __name__ == "__main__":
    # 这个脚本需要在有WebDriver实例的情况下运行
    # 可以通过以下方式获取driver:
    # 1. 从现有的测试中获取
    # 2. 连接到设备后获取
    # 3. 手动创建WebDriver实例
    
    logger.info("请在有WebDriver实例的环境中运行此测试")
    logger.info("示例用法:")
    logger.info("1. 在现有测试中导入此模块")
    logger.info("2. 调用 test_visible_page_methods(driver)")
    logger.info("3. 查看性能对比结果") 