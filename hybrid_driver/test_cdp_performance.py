#!/usr/bin/env python3
"""
CDP协议性能测试脚本 - 比较CDP方法和传统方法的性能
"""

import time
import asyncio
from hybrid_driver.device_pool import DevicePool
from hybrid_driver.api.models import ConnectConfig
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)

async def test_cdp_performance():
    """测试CDP协议方法性能"""
    logger.info("🚀 开始CDP协议性能测试")
    
    # 连接设备
    config = ConnectConfig(
        serial_id="47.94.130.125:6521",
        user_id="0",
        android_process="com.tencent.mm:appbrand0"
    )
    
    device = DevicePool().connect(config)
    driver = device._web_execute._driver
    
    try:
        # 测试CDP基础方法
        logger.info("📋 测试 get_visible_page_cdp")
        start_time = time.time()
        result = WebDriverUtils.get_visible_page_cdp(driver, 1)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        logger.info(f"✅ CDP基础方法结果: {result}")
        logger.info(f"⏱️ CDP基础方法耗时: {execution_time_ms:.2f}ms")
        
        # 测试CDP增强方法
        logger.info("📋 测试 get_visible_page_cdp_enhanced")
        start_time = time.time()
        result = WebDriverUtils.get_visible_page_cdp_enhanced(driver, 1)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        logger.info(f"✅ CDP增强方法结果: {result}")
        logger.info(f"⏱️ CDP增强方法耗时: {execution_time_ms:.2f}ms")
        
        # 测试最简单方法（对比）
        logger.info("📋 测试 get_visible_page_simple")
        start_time = time.time()
        result = WebDriverUtils.get_visible_page_simple(driver, 2)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        logger.info(f"✅ 最简单方法结果: {result}")
        logger.info(f"⏱️ 最简单方法耗时: {execution_time_ms:.2f}ms")
        
        # 测试快速方法（对比）
        logger.info("📋 测试 get_visible_page_fast")
        start_time = time.time()
        result = WebDriverUtils.get_visible_page_fast(driver, 3)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        logger.info(f"✅ 快速方法结果: {result}")
        logger.info(f"⏱️ 快速方法耗时: {execution_time_ms:.2f}ms")
        
        # 测试标准方法（对比）
        logger.info("📋 测试 get_visible_page")
        start_time = time.time()
        result = WebDriverUtils.get_visible_page(driver, 10)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        logger.info(f"✅ 标准方法结果: {result}")
        logger.info(f"⏱️ 标准方法耗时: {execution_time_ms:.2f}ms")
        
        # 测试CDP命令的原始性能
        logger.info("📋 测试原始CDP命令性能")
        start_time = time.time()
        
        try:
            # 获取所有目标
            targets = driver.execute_cdp_cmd('Target.getTargets', {})
            target_infos = targets.get('targetInfos', [])
            page_targets = [t for t in target_infos if t.get('type') == 'page']
            
            logger.info(f"📋 总目标数: {len(target_infos)}")
            logger.info(f"📋 页面目标数: {len(page_targets)}")
            
            # 检查第一个页面目标
            if page_targets:
                target = page_targets[0]
                target_id = target['targetId']
                logger.info(f"📋 第一个页面目标: {target_id}")
                
                # 尝试附加
                if not target.get('attached'):
                    attach_result = driver.execute_cdp_cmd('Target.attachToTarget', {
                        'targetId': target_id, 
                        'flatten': True
                    })
                    session_id = attach_result.get('sessionId')
                    logger.info(f"📋 附加结果: {session_id}")
                    
                    if session_id:
                        # 执行脚本
                        script_result = driver.execute_cdp_cmd('Runtime.evaluate', {
                            'expression': 'document.title',
                            'sessionId': session_id
                        })
                        title = script_result.get('result', {}).get('value', '')
                        logger.info(f"📋 页面标题: {title}")
                        
        except Exception as e:
            logger.error(f"❌ 原始CDP命令测试失败: {e}")
        
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000
        logger.info(f"⏱️ 原始CDP命令耗时: {execution_time_ms:.2f}ms")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
    finally:
        driver.quit()

def main():
    """主函数"""
    logger.info("🎯 开始CDP协议性能测试")
    asyncio.run(test_cdp_performance())
    logger.info("🏁 CDP协议性能测试完成")

if __name__ == "__main__":
    main() 