#!/usr/bin/env python3
"""
测试访问京东网站 - 基于 test_scaling.py 的代码
"""
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import wait
from datetime import datetime
import queue

from selenium.webdriver.remote.file_detector import LocalFileDetector
from selenium.webdriver.support import expected_conditions as EC, wait


def get_timestamp():
    """获取当前时间戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def log_with_timestamp(message):
    """带时间戳的日志输出"""
    timestamp = get_timestamp()
    print(f"[{timestamp}] {message}")

def create_jd_session_concurrent(session_id, start_barrier):
    """创建单个 Selenium 会话访问京东网站 - 并发版本"""
    log_with_timestamp(f"🚀 会话 {session_id}: 准备就绪，等待并发启动...")
    
    # 等待所有线程准备就绪
    start_barrier.wait()
    
    log_with_timestamp(f"🚀 会话 {session_id}: 开始创建...")
    
    # 用户特定的存储路径 - 让 Chrome 自己创建目录，添加时间戳确保唯一性
    import time
    timestamp = int(time.time() * 1000)  # 毫秒时间戳
    user_data_dir = f"/opt/chrome_user_data/chrome/session_{session_id}_{timestamp}_gongcong"
    
    log_with_timestamp(f"📁 会话 {session_id}: 使用用户数据目录: {user_data_dir}")
    
    # 配置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # 用户特定的存储路径 - Chrome 会自动创建必要的子目录
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
    
    # 性能优化配置
    chrome_options.add_argument('--disable-images')  # 禁用图片加载
    chrome_options.add_argument('--disable-plugins')  # 禁用插件
    chrome_options.add_argument('--disable-extensions')  # 禁用扩展
    chrome_options.add_argument('--disable-background-timer-throttling')  # 禁用后台定时器节流
    chrome_options.add_argument('--disable-renderer-backgrounding')  # 禁用渲染器后台化
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')  # 禁用被遮挡窗口的后台化
    chrome_options.add_argument('--disable-ipc-flooding-protection')  # 禁用IPC洪水保护
    chrome_options.add_argument('--aggressive-cache-discard')  # 激进缓存丢弃
    chrome_options.add_argument('--memory-pressure-off')  # 关闭内存压力检测
    
    # 网络优化
    chrome_options.add_argument('--max-connections-per-host=6')  # 限制每个主机的连接数
    chrome_options.add_argument('--disable-background-networking')  # 禁用后台网络
    
    # 证书和SSL相关配置
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_argument('--disable-web-security')
    
    # 设置页面加载超时
    chrome_options.add_argument('--page-load-strategy=eager')  # 使用eager策略，不等待所有资源
    
    chrome_options.page_load_strategy = 'eager'   # 关键

    try:
        # 记录开始连接时间
        connection_start_time = time.time()
        log_with_timestamp(f"📡 会话 {session_id}: 开始连接到 Selenium Grid...")
        
        # 连接到 Selenium Grid（使用 localhost）
        driver = webdriver.Remote(
            command_executor='http://172.16.1.129:30444/wd/hub',
            options=chrome_options
        )
        
        # 设置页面加载超时时间（秒）
        driver.set_page_load_timeout(30)  # 30秒超时
        driver.implicitly_wait(10)  # 隐式等待10秒
        
        # 计算连接时间
        connection_time = time.time() - connection_start_time
        log_with_timestamp(f"✅ 会话 {session_id}: 连接成功！连接耗时: {connection_time:.3f} 秒")
        log_with_timestamp(f"📄 会话 {session_id}: chrome driver session : {driver.session_id}")
        
        # 记录浏览器打开开始时间
        browser_start_time = time.time()


        driver.get('https://qifu-api.baidubce.com/ip/local/geo/v1/district')

        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            ip_info = json.loads(body_text)
            log_with_timestamp(f"📄 会话 {session_id}: IP信息: {ip_info}")
        except Exception as e:
            log_with_timestamp(f"⚠️  会话 {session_id}: IP检查异常: {e}")

        url = 'https://www.taobao.com/'
        log_with_timestamp(f"🌐 会话 {session_id}: 开始打开  {url}")
        
        driver.file_detector = LocalFileDetector()
        file_path = str(Path("logo.png").resolve())


        # 访问京东网站
        driver.get(url)

        # 计算浏览器打开时间
        browser_time = time.time() - browser_start_time
        log_with_timestamp(f"✅ 会话 {session_id}: 京东网站访问成功！访问耗时: {browser_time:.3f} 秒")

        # 1) 先点击搜同款按钮打开图片搜索弹框
        log_with_timestamp(f"🔍 会话 {session_id}: 开始查找搜同款按钮...")
        try:
            search_btn = wait.WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "image-search-icon-outerMode"))
            )
            search_btn.click()
            log_with_timestamp(f"✅ 会话 {session_id}: 成功点击搜同款按钮，打开图片搜索弹框")
        except Exception as e:
            log_with_timestamp(f"❌ 会话 {session_id}: 未找到搜同款按钮: {e}")
            return f"会话 {session_id} 失败 - 未找到搜同款按钮"

        # 2) 等待弹框出现并找到隐藏的file input
        log_with_timestamp(f"🔍 会话 {session_id}: 等待图片搜索弹框出现...")
        try:
            file_input = wait.WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "image-search-custom-file-input"))
            )
            log_with_timestamp(f"✅ 会话 {session_id}: 成功找到隐藏的file input (ID: image-search-custom-file-input)")
        except Exception as e:
            log_with_timestamp(f"❌ 会话 {session_id}: 未找到file input: {e}")
            return f"会话 {session_id} 失败 - 未找到file input"

        # 3) 显示隐藏的file input
        log_with_timestamp(f"🔧 会话 {session_id}: 显示隐藏的file input...")
        try:
            driver.execute_script("""
            arguments[0].style.display='block';
            arguments[0].style.visibility='visible';
            arguments[0].removeAttribute('disabled');
            """, file_input)
            log_with_timestamp(f"✅ 会话 {session_id}: 成功显示file input")
        except Exception as e:
            log_with_timestamp(f"⚠️  会话 {session_id}: 显示file input时出现异常: {e}")

        # 4) 上传文件
        log_with_timestamp(f"📁 会话 {session_id}: 开始上传文件: {file_path}")
        try:
            file_input.send_keys(file_path)
            log_with_timestamp(f"✅ 会话 {session_id}: 文件路径已设置到file input")
        except Exception as e:
            log_with_timestamp(f"❌ 会话 {session_id}: 文件上传失败: {e}")
            return f"会话 {session_id} 失败 - 文件上传失败"

        # 5) 等待上传完成，查找搜索按钮
        log_with_timestamp(f"⏳ 会话 {session_id}: 等待上传完成，查找搜索按钮...")
        try:
            search_button = wait.WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "image-search-upload-button"))
            )
            log_with_timestamp(f"✅ 会话 {session_id}: 找到搜索按钮 (ID: image-search-upload-button)")
            
            # 点击搜索按钮
            search_button.click()
            log_with_timestamp(f"✅ 会话 {session_id}: 搜索按钮点击成功")
        except Exception as e:
            log_with_timestamp(f"❌ 会话 {session_id}: 未找到或无法点击搜索按钮: {e}")
            return f"会话 {session_id} 失败 - 搜索按钮操作失败"

        # 6) 等待搜索结果页面加载
        log_with_timestamp(f"⏳ 会话 {session_id}: 等待搜索结果页面加载...")
        time.sleep(5)  # 等待5秒让搜索结果加载
        
        # 7) 检查搜索结果
        try:
            current_url = driver.current_url
            log_with_timestamp(f"🔗 会话 {session_id}: 当前URL: {current_url}")
            
            if "search" in current_url.lower() or "result" in current_url.lower():
                log_with_timestamp(f"✅ 会话 {session_id}: 图片搜索成功，已跳转到搜索结果页面")
            else:
                log_with_timestamp(f"ℹ️  会话 {session_id}: 图片搜索完成，当前页面: {current_url}")
        except Exception as e:
            log_with_timestamp(f"⚠️  会话 {session_id}: 检查搜索结果时出现异常: {e}")
        


        # 获取页面标题
        title = driver.title
        log_with_timestamp(f"📄 会话 {session_id}: 页面标题: {title}")
        
        # 获取页面URL
        current_url = driver.current_url
        log_with_timestamp(f"🔗 会话 {session_id}: 当前URL: {current_url}")
        
        # 尝试获取页面的一些基本信息
        try:
            # 获取页面源码长度
            page_source_length = len(driver.page_source)
            log_with_timestamp(f"📊 会话 {session_id}: 页面源码长度: {page_source_length} 字符")
        
                
        except Exception as e:
            log_with_timestamp(f"⚠️  会话 {session_id}: 页面信息获取异常: {e}")
        
        # 保持会话活跃一段时间
        log_with_timestamp(f"⏳ 会话 {session_id}: 保持活跃 10 秒...")
        time.sleep(90)
        
        # 关闭会话
        # driver.quit()
        log_with_timestamp(f"🔒 会话 {session_id}: 已关闭")
        
        # 总结时间统计
        total_time = connection_time + browser_time
        log_with_timestamp(f"📊 会话 {session_id}: 时间统计 - 连接: {connection_time:.3f}s, 浏览器: {browser_time:.3f}s, 总计: {total_time:.3f}s")
        
        return f"会话 {session_id} 完成 - 连接: {connection_time:.3f}s, 浏览器: {browser_time:.3f}s"
        
    except Exception as e:
        error_msg = f"❌ 会话 {session_id} 失败: {e}"
        log_with_timestamp(error_msg)
        return error_msg
    finally:
        log_with_timestamp("finnal quit driver")
        driver.quit()    

def test_jd_concurrent_scaling(concurrent_count=5):
    """测试并发访问京东网站功能 - 真正并发版本"""
    log_with_timestamp(f"🚀 开始测试 Selenium Grid 并发访问京东网站...")
    log_with_timestamp(f"📊 并发数: {concurrent_count}")
    
    # 创建同步屏障，确保所有线程同时启动
    start_barrier = threading.Barrier(concurrent_count)
    
    # 记录总体开始时间
    overall_start_time = time.time()
    
    # 使用线程池执行并发测试
    with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
        # 提交所有任务
        future_to_session = {
            executor.submit(create_jd_session_concurrent, i+1, start_barrier): i+1 
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
    log_with_timestamp("🎉 京东网站并发访问测试完成！")

if __name__ == "__main__":
    # 设置并发数为 6
    test_jd_concurrent_scaling(concurrent_count=1)
