#!/usr/bin/env python3
"""
测试 Selenium Grid 扩容功能 - 真正并发版本
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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

def create_session_concurrent(session_id, start_barrier):
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
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # 用户特定的存储路径 - Chrome 会自动创建必要的子目录
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')

    chrome_options.add_experimental_option("useAutomationExtension", False)
    # 排除 enable-automation 这个 switch
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # 动态代理配置 - 每个会话使用不同的代理IP进行测试
    proxy_configs = [
        {"ip": "180.158.94.91", "port": "40013","username":"vgmpgv","password":"1bk79g9y"}
    ]
    
    # 根据会话ID选择代理配置
    proxy_config = proxy_configs[0]
    
    # 添加动态代理配置到capabilities
    chrome_options.set_capability("se:proxyConfig", proxy_config)
    
    try:
        # 记录开始连接时间
        connection_start_time = time.time()
        log_with_timestamp(f"📡 会话 {session_id}: 开始连接到 Selenium Grid...")
        
        # 连接到 Selenium Grid（使用 localhost）
        driver = webdriver.Remote(
            command_executor='http://172.16.1.129:30444/wd/hub',
            options=chrome_options
        )
        
        session = driver.session_id

        # 计算连接时间
        connection_time = time.time() - connection_start_time
        log_with_timestamp(f"✅ 会话 {session_id}: 连接成功！连接耗时: {connection_time:.3f} 秒")
        log_with_timestamp(f"📄 会话 {session_id}: chrome driver session : {driver.session_id}")
        
        # 记录浏览器打开开始时间
        browser_start_time = time.time()
        log_with_timestamp(f"🌐 会话 {session_id}: 开始打开浏览器页面...")
        
        # 测试代理功能 - 访问 IP 检查页面 (使用httpbin.org替代不可用的百度接口)
        driver.get('https://httpbin.org/ip')
        
        # 计算浏览器打开时间
        browser_time = time.time() - browser_start_time
        log_with_timestamp(f"✅ 会话 {session_id}: 浏览器页面打开成功！打开耗时: {browser_time:.3f} 秒")
        
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            ip_info = json.loads(body_text)
            current_ip = ip_info.get('origin', '未知')
            log_with_timestamp(f"📄 会话 {session_id}: 当前出口IP: {current_ip}")
            log_with_timestamp(f"📄 会话 {session_id}: 完整IP信息: {ip_info}")
        except Exception as e:
            log_with_timestamp(f"⚠️  会话 {session_id}: IP检查异常: {e}")
            # 备用方案：尝试使用纯文本接口
            try:
                driver.get('https://checkip.amazonaws.com')
                ip_text = driver.find_element(By.TAG_NAME, "body").text.strip()
                log_with_timestamp(f"📄 会话 {session_id}: 当前出口IP (备用): {ip_text}")
            except Exception as backup_e:
                log_with_timestamp(f"⚠️  会话 {session_id}: 备用IP检查也失败: {backup_e}")
        
        # 获取页面标题
        title = driver.title
        log_with_timestamp(f"📄 会话 {session_id}: 页面标题: {title}")
        
        # 保持会话活跃一段时间
        log_with_timestamp(f"⏳ 会话 {session_id}: 保持活跃 30 秒...")
        # time.sleep(30)
        
        # driver.get("https://www.jd.com/")

        # time.sleep(600)
        # 关闭会话
        driver.quit()
        log_with_timestamp(f"🔒 会话 {session_id}: 已关闭")
        
        # 总结时间统计
        total_time = connection_time + browser_time
        log_with_timestamp(f"📊 会话 {session_id}: 时间统计 - 连接: {connection_time:.3f}s, 浏览器: {browser_time:.3f}s, 总计: {total_time:.3f}s")
        
        return f"会话 {session_id} 完成 - 连接: {connection_time:.3f}s, 浏览器: {browser_time:.3f}s"
        
    except Exception as e:
        error_msg = f"❌ 会话 {session_id} 失败: {e}"
        log_with_timestamp(error_msg)
        driver.quit()
        return error_msg

def test_concurrent_scaling(concurrent_count=1):
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
            executor.submit(create_session_concurrent, i+1, start_barrier): i+1 
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
    log_with_timestamp("🎉 并发扩容测试完成！")

if __name__ == "__main__":
    # 设置并发数为 10
    test_concurrent_scaling(concurrent_count=1)
