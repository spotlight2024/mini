#!/usr/bin/env python3
"""
测试 Selenium Grid 扩容功能 - 真正并发版本
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import argparse
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from selenium.webdriver.common.by import By
from datetime import datetime
import queue

def get_timestamp():
    """获取当前时间戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def log_with_timestamp(message):
    """带时间戳的日志输出"""
    timestamp = get_timestamp()
    print(f"[{timestamp}] {message}")

def create_session_concurrent(session_id, start_barrier, *, target_url=None, keep_alive=0):
    """创建单个 Selenium 会话 - 并发版本"""
    log_with_timestamp(f"🚀 会话 {session_id}: 准备就绪，等待并发启动...")
    
    # 等待所有线程准备就绪
    start_barrier.wait()
    
    log_with_timestamp(f"🚀 会话 {session_id}: 开始创建...")
    
    # 用户特定的存储路径 - 让 Chrome 自己创建目录
    user_data_dir = f"/opt/chrome_user_data/chrome/session_{session_id}_gongcong"
    
    log_with_timestamp(f"📁 会话 {session_id}: 使用用户数据目录: {user_data_dir}")
    
    # 配置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # 用户特定的存储路径 - Chrome 会自动创建必要的子目录
    # chrome_options.add_argument(f'--user-data-dir={user_data_dir}')

    chrome_options.add_experimental_option("useAutomationExtension", False)
    # 排除 enable-automation 这个 switch
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # 动态代理配置 - 每个会话使用不同的代理IP进行测试
    proxy_configs = [
        # {"ip": "180.158.94.91", "port": "40013","username":"vgmpgv","password":"1bk79g9y"}
        {"ip": "192.168.1.78", "port": "7897"}
    ]
    
    # 根据会话ID选择代理配置
    proxy_config = proxy_configs[0]
    
    # 添加动态代理配置到capabilities
    # chrome_options.set_capability("se:proxyConfig", proxy_config)
    
    driver = None
    try:
        # 记录开始连接时间
        connection_start_time = time.time()
        log_with_timestamp(f"📡 会话 {session_id}: 开始连接到 Selenium Grid...")
        
        # 连接到 Selenium Grid（使用 localhost）
        driver = webdriver.Remote(
            command_executor='http://172.16.1.129:30444/wd/hub',
            options=chrome_options
        )

        # 计算连接时间
        connection_time = time.time() - connection_start_time
        log_with_timestamp(f"✅ 会话 {session_id}: 连接成功！连接耗时: {connection_time:.3f} 秒")
        log_with_timestamp(f"📄 会话 {session_id}: chrome driver session : {driver.session_id}")
        
        browser_time = 0.0
        if target_url:
            browser_start_time = time.time()
            log_with_timestamp(f"🌐 会话 {session_id}: 开始打开页面 {target_url}...")
            driver.get(target_url)
            browser_time = time.time() - browser_start_time
            log_with_timestamp(f"✅ 会话 {session_id}: 页面打开成功！耗时: {browser_time:.3f} 秒")
            log_with_timestamp(f"📄 会话 {session_id}: 页面标题: {driver.title}")

        if keep_alive > 0:
            log_with_timestamp(f"⏳ 会话 {session_id}: 保持活跃 {keep_alive} 秒...")
            time.sleep(keep_alive)
        
        # driver.get("https://www.jd.com/")

        # time.sleep(600)
        # 关闭会话
        driver.quit()
        log_with_timestamp(f"🔒 会话 {session_id}: 已关闭")
        
        # 总结时间统计
        total_time = connection_time + browser_time
        log_with_timestamp(f"📊 会话 {session_id}: 时间统计 - 连接: {connection_time:.3f}s, 浏览器: {browser_time:.3f}s, 总计: {total_time:.3f}s")
        
        return {
            "session_id": session_id,
            "status": "success",
            "connection_time": connection_time,
            "browser_time": browser_time,
            "total_time": total_time,
        }

    except Exception as e:
        error_msg = f"❌ 会话 {session_id} 失败: {e}"
        log_with_timestamp(error_msg)
        if driver is not None:
            driver.quit()
        return {
            "session_id": session_id,
            "status": "error",
            "error": str(e),
        }

def test_concurrent_scaling(*, concurrent_count=1, target_url=None, keep_alive=0):
    """测试并发扩容功能 - 真正并发版本"""
    log_with_timestamp(f"🚀 开始测试 Selenium Grid 并发扩容功能...")
    log_with_timestamp(f"📊 并发数: {concurrent_count}")
    
    # 创建同步屏障，确保所有线程同时启动
    start_barrier = threading.Barrier(concurrent_count)
    
    # 记录总体开始时间
    overall_start_time = time.time()
    
    # 使用线程池执行并发测试
    with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
        # 提交所有任务
        future_to_session = {
            executor.submit(
                create_session_concurrent,
                i + 1,
                start_barrier,
                target_url=target_url,
                keep_alive=keep_alive,
            ): i + 1
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
                if result.get("status") == "success":
                    log_with_timestamp(
                        f"✅ 会话 {session_id} 完成 - 连接: {result['connection_time']:.3f}s, "
                        f"浏览器: {result['browser_time']:.3f}s"
                    )
                else:
                    log_with_timestamp(f"❌ 会话 {session_id} 执行异常: {result.get('error')}")
            except Exception as e:
                error_msg = f"❌ 会话 {session_id} 执行异常: {e}"
                log_with_timestamp(error_msg)
                results.append({
                    "session_id": session_id,
                    "status": "error",
                    "error": str(e),
                })
    
    # 计算总体耗时
    overall_time = time.time() - overall_start_time
    
    # 统计结果
    success_records = [r for r in results if r.get("status") == "success"]
    success_count = len(success_records)
    error_count = len(results) - success_count
    
    log_with_timestamp("\n📊 测试结果统计:")
    log_with_timestamp(f"✅ 成功: {success_count}")
    log_with_timestamp(f"❌ 失败: {error_count}")
    log_with_timestamp(f"🎯 总并发: {concurrent_count}")
    log_with_timestamp(f"⏱️  总体耗时: {overall_time:.3f} 秒")

    if success_records:
        log_with_timestamp("\n📈 成功会话耗时明细 (单位: 秒):")
        for record in sorted(success_records, key=lambda r: r["total_time"], reverse=True):
            log_with_timestamp(
                f"会话 {record['session_id']:>2} -> 连接 {record['connection_time']:.3f}, "
                f"页面 {record['browser_time']:.3f}, 总计 {record['total_time']:.3f}"
            )

        total_times = [r["total_time"] for r in success_records]
        avg_time = sum(total_times) / len(total_times)
        fastest = min(total_times)
        slowest = max(total_times)
        log_with_timestamp(
            f"\n📌 汇总 - 平均 {avg_time:.3f}s, 最快 {fastest:.3f}s, 最慢 {slowest:.3f}s"
        )

    log_with_timestamp("🎉 并发扩容测试完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Selenium Grid 并发扩容测试")
    parser.add_argument("--concurrency", type=int, default=1, help="并发会话数")
    parser.add_argument(
        "--url",
        type=str,
        default="",
        help="需要打开的页面，留空表示仅建立会话",
    )
    parser.add_argument(
        "--keep-alive",
        type=int,
        default=0,
        help="会话保持时长（秒）",
    )
    args = parser.parse_args()

    test_concurrent_scaling(
        concurrent_count=args.concurrency,
        target_url=args.url or None,
        keep_alive=args.keep_alive,
    )
