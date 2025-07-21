#!/usr/bin/env python3
"""
简单CDP协议测试脚本 - 测试CDP命令的基本功能
"""

import time
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)

def test_cdp_commands(driver):
    """测试CDP命令"""
    logger.info("🔧 开始测试CDP命令")
    
    try:
        # 1. 测试 Target.getTargets
        logger.info("📋 测试 Target.getTargets 命令")
        start_time = time.time()
        
        targets = driver.execute_cdp_cmd('Target.getTargets', {})
        cdp_time = (time.time() - start_time) * 1000
        
        logger.info(f"✅ Target.getTargets 执行成功，耗时: {cdp_time:.2f}ms")
        logger.info(f"📋 获取到 {len(targets.get('targetInfos', []))} 个目标")
        
        # 2. 分析目标信息
        target_infos = targets.get('targetInfos', [])
        page_targets = [t for t in target_infos if t.get('type') == 'page']
        attached_targets = [t for t in target_infos if t.get('attached')]
        
        logger.info(f"📋 页面类型目标: {len(page_targets)}")
        logger.info(f"📋 已附加目标: {len(attached_targets)}")
        
        # 3. 显示目标详情
        for i, target in enumerate(target_infos):
            logger.info(f"📋 目标 {i+1}: {target}")
        
        # 4. 测试页面目标
        if page_targets:
            logger.info("📋 测试页面目标")
            target = page_targets[0]
            target_id = target['targetId']
            
            logger.info(f"📋 选择页面目标: {target_id}")
            logger.info(f"📋 目标信息: {target}")
            
            # 5. 测试附加到目标
            if not target.get('attached'):
                logger.info("📋 尝试附加到目标...")
                attach_start = time.time()
                
                try:
                    attach_result = driver.execute_cdp_cmd('Target.attachToTarget', {
                        'targetId': target_id, 
                        'flatten': True
                    })
                    attach_time = (time.time() - attach_start) * 1000
                    
                    logger.info(f"✅ 附加成功，耗时: {attach_time:.2f}ms")
                    logger.info(f"📋 附加结果: {attach_result}")
                    
                    session_id = attach_result.get('sessionId')
                    if session_id:
                        # 6. 测试执行脚本
                        logger.info("📋 测试执行脚本...")
                        script_start = time.time()
                        
                        script_result = driver.execute_cdp_cmd('Runtime.evaluate', {
                            'expression': 'document.title',
                            'sessionId': session_id
                        })
                        script_time = (time.time() - script_start) * 1000
                        
                        logger.info(f"✅ 脚本执行成功，耗时: {script_time:.2f}ms")
                        logger.info(f"📋 脚本结果: {script_result}")
                        
                        title = script_result.get('result', {}).get('value', '')
                        logger.info(f"📋 页面标题: {title}")
                        
                        if ":VISIBLE" in title:
                            logger.info(f"✅ 找到可见页面: {target_id}")
                            return target_id
                        else:
                            logger.info(f"❌ 页面不可见: {title}")
                    else:
                        logger.warning("❌ 附加失败，未获取到sessionId")
                        
                except Exception as e:
                    attach_time = (time.time() - attach_start) * 1000
                    logger.error(f"❌ 附加失败: {e}")
                    logger.info(f"⏱️ 附加耗时: {attach_time:.2f}ms")
            else:
                logger.info("📋 目标已附加，直接测试脚本执行")
                script_start = time.time()
                
                try:
                    script_result = driver.execute_cdp_cmd('Runtime.evaluate', {
                        'expression': 'document.title'
                    })
                    script_time = (time.time() - script_start) * 1000
                    
                    logger.info(f"✅ 脚本执行成功，耗时: {script_time:.2f}ms")
                    logger.info(f"📋 脚本结果: {script_result}")
                    
                    title = script_result.get('result', {}).get('value', '')
                    logger.info(f"📋 页面标题: {title}")
                    
                    if ":VISIBLE" in title:
                        logger.info(f"✅ 找到可见页面: {target_id}")
                        return target_id
                    else:
                        logger.info(f"❌ 页面不可见: {title}")
                        
                except Exception as e:
                    script_time = (time.time() - script_start) * 1000
                    logger.error(f"❌ 脚本执行失败: {e}")
                    logger.info(f"⏱️ 脚本执行耗时: {script_time:.2f}ms")
        else:
            logger.warning("❌ 未找到页面类型目标")
        
        return None
        
    except Exception as e:
        logger.error(f"❌ CDP命令测试失败: {e}")
        return None

def main():
    """主函数 - 需要在有driver的环境中调用"""
    logger.info("🎯 CDP协议测试脚本")
    logger.info("📝 使用方法: 在现有环境中调用 test_cdp_commands(driver)")

if __name__ == "__main__":
    main() 