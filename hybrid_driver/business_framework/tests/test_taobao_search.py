"""
淘宝搜索业务测试 - 基于新框架实现jd_test_actions.py的逻辑
"""
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from hybrid_driver.business_framework.business.taobao_business import TaobaoBusiness
from hybrid_driver.log_config import get_logger


def create_taobao_session_with_actions(session_id: int, start_barrier: threading.Barrier):
    """使用ActionChains创建淘宝会话 - 基于jd_test_actions.py的逻辑"""
    def log_with_timestamp(message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")
    
    log_with_timestamp(f"🚀 会话 {session_id}: 准备就绪，等待并发启动...")
    start_barrier.wait()
    
    log_with_timestamp(f"🚀 会话 {session_id}: 开始创建...")
    
    # 创建淘宝业务实例
    user_id = f"test_user_{session_id}"
    taobao_business = TaobaoBusiness(session_id, user_id)
    
    try:
        # 记录开始连接时间
        connection_start_time = time.time()
        log_with_timestamp(f"📡 会话 {session_id}: 开始连接到 Selenium Grid...")
        
        # 初始化
        taobao_business.initialize()
        taobao_business.initialize_pages()

        # 计算连接时间
        connection_time = time.time() - connection_start_time
        log_with_timestamp(f"✅ 会话 {session_id}: 连接成功！连接耗时: {connection_time:.3f} 秒")
        
        # 记录浏览器打开开始时间
        browser_start_time = time.time()
        
        # 执行图片搜索流程（使用ActionChains）
        success = taobao_business.execute_image_search_with_actions("logo.png")
        
        # 计算浏览器时间
        browser_time = time.time() - browser_start_time
        log_with_timestamp(f"✅ 淘宝网站访问成功！访问耗时: {browser_time:.3f} 秒")
        
        # 保持会话活跃
        log_with_timestamp(f"⏳ 会话 {session_id}: 保持活跃 90 秒...")
        time.sleep(60)
        
        # 计算总时间
        total_time = connection_time + browser_time
        log_with_timestamp(f"📊 会话 {session_id}: 时间统计 - 连接: {connection_time:.3f}s, 浏览器: {browser_time:.3f}s, 总计: {total_time:.3f}s")
        
        if success:
            return f"会话 {session_id} 完成 - 连接: {connection_time:.3f}s, 浏览器: {browser_time:.3f}s"
        else:
            return f"会话 {session_id} 失败 - 搜索业务执行失败"
        
    except Exception as e:
        error_msg = f"❌ 会话 {session_id} 失败: {e}"
        log_with_timestamp(error_msg)
        return error_msg
    finally:
        # 清理资源
        taobao_business.cleanup()


def test_taobao_concurrent_with_actions(concurrent_count: int = 1):
    """测试并发访问淘宝网站功能 - ActionChains版本"""
    def log_with_timestamp(message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")
    
    log_with_timestamp(f"🚀 开始测试 Selenium Grid 并发访问淘宝网站（ActionChains版本）...")
    log_with_timestamp(f"📊 并发数: {concurrent_count}")
    
    # 创建同步屏障，确保所有线程同时启动
    start_barrier = threading.Barrier(concurrent_count)
    
    # 记录总体开始时间
    overall_start_time = time.time()
    
    # 使用线程池执行并发测试
    with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
        # 提交所有任务
        future_to_session = {
            executor.submit(create_taobao_session_with_actions, i+1, start_barrier): i+1 
            for i in range(concurrent_count)
        }
        
        log_with_timestamp(f"🎯 已提交 {concurrent_count} 个并发任务，等待所有线程准备就绪...")
        
        # 收集结果
        results = []
        for future in as_completed(future_to_session):
            session_id = future_to_session[future]
            try:
                result = future.result()
                results.append(result)
                log_with_timestamp(f"✅ {result}")
            except Exception as e:
                error_msg = f"❌ 会话 {session_id} 执行异常: {e}"
                log_with_timestamp(error_msg)
                results.append(error_msg)
    
    # 计算总体耗时
    overall_time = time.time() - overall_start_time
    
    # 统计结果
    success_count = sum(1 for r in results if "完成" in r)
    error_count = len(results) - success_count
    
    log_with_timestamp(f"\n📊 测试结果统计:")
    log_with_timestamp(f"✅ 成功: {success_count}")
    log_with_timestamp(f"❌ 失败: {error_count}")
    log_with_timestamp(f"🎯 总并发: {concurrent_count}")
    log_with_timestamp(f"⏱️  总体耗时: {overall_time:.3f} 秒")
    log_with_timestamp("🎉 淘宝网站并发访问测试完成！")


if __name__ == "__main__":
    # 设置并发数为 1
    test_taobao_concurrent_with_actions(concurrent_count=1)
