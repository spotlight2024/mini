#!/usr/bin/env python3
"""
淘宝搜索测试 API - 通过 HTTP 接口调用淘宝搜索功能
"""
import time
import uuid
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from hybrid_driver.business_framework.business.taobao_business import TaobaoBusiness
from hybrid_driver.log_config import get_logger
from hybrid_driver.proxy.proxy_provider import get_proxy_config_for_selenium, ProxyProviderNames

# 创建路由器
router = APIRouter(prefix="/test/taobao", tags=["淘宝搜索测试"])
logger = get_logger(__name__)

class TaobaoSearchResponse(BaseModel):
    """淘宝搜索响应模型"""
    success: bool = Field(description="是否成功")
    uid: str = Field(description="用户ID")
    connection_time: float = Field(description="连接耗时（秒）")
    browser_time: float = Field(description="浏览器操作耗时（秒）")
    total_time: float = Field(description="总耗时（秒）")
    image_path: str = Field(description="搜索图片路径")
    start_time: str = Field(description="开始时间")
    end_time: str = Field(description="结束时间")
    error: Optional[str] = Field(default=None, description="错误信息")
    message: str = Field(description="执行消息")
    screen_shot_url: Optional[str] = Field(default=None, description="截图文件URL路径")
    product_titles: Optional[List[str]] = Field(default=None, description="商品标题列表")
    product_count: int = Field(default=0, description="商品数量")


def log_with_timestamp(message: str, session_id: int = None):
    """带时间戳的日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    prefix = f"[会话{session_id}] " if session_id else ""
    log_message = f"[{timestamp}] {prefix}{message}"
    print(log_message)
    logger.info(log_message)




def sync_taobao_search_task(uid: str, image_path: str, timeout: int, proxy_provider: str = ProxyProviderNames.TIANQI) -> TaobaoSearchResponse:
    """
    同步执行淘宝搜索任务
    
    Args:
        uid: 用户ID
        image_path: 图片路径
        timeout: 超时时间
        proxy_provider: 代理提供者名称，可选值：
            - ProxyProviderNames.TIANQI: 天启代理（默认）
            - ProxyProviderNames.JULIANG: 巨量代理
            - "tianqi": 天启代理（字符串形式）
            - "juliang": 巨量代理（字符串形式）
    """
    session_id = uid

    snapshot_id = session_id + "_" + uuid.uuid4().hex
    screenshot_filename = f"screenshot_{snapshot_id}.png"
    screenshot_path = f"/app/@web_screenshot/{screenshot_filename}"
    screen_shot_url = f"/@web_screenshot/{screenshot_filename}"
    start_time = datetime.now()
    
    try:
        
        # 处理图片路径
        if not os.path.isabs(image_path):
            # 从api/test目录查找test_img目录
            api_dir = os.path.dirname(os.path.abspath(__file__))
            test_img_dir = os.path.join(api_dir, "test_img")
            full_image_path = os.path.join(test_img_dir, image_path)
        else:
            full_image_path = image_path
        
        logger.info(f"[会话{session_id}] 开始执行淘宝搜索任务，图片路径: {full_image_path}")
        
        # 检查图片文件
        if not os.path.exists(full_image_path):
            error_msg = f"图片文件不存在: {full_image_path}"
            return TaobaoSearchResponse(
                success=False,
                uid=uid,
                connection_time=0.0,
                browser_time=0.0,
                total_time=0.0,
                image_path=image_path,
                start_time=start_time.isoformat(),
                end_time=datetime.now().isoformat(),
                error=error_msg,
                message=error_msg,
                screen_shot_url=None,
                product_titles=None,
                product_count=0
            )
        
        # 创建淘宝业务实例
        taobao_business = TaobaoBusiness(session_id)
        
        # 获取代理配置
        logger.info(f"[会话{session_id}] 获取代理IP配置，使用提供者: {proxy_provider}")
        proxy_config = get_proxy_config_for_selenium(proxy_provider)

        if proxy_config:
            logger.info(f"[会话{session_id}] 获取到代理IP: {proxy_config['ip']}:{proxy_config['port']} ({proxy_config.get('region', 'unknown')})")

            # 配置Chrome代理选项
            chrome_options = taobao_business.get_chrome_options()
            chrome_options.set_capability("se:proxyConfig", proxy_config)

            logger.info(f"[会话{session_id}] 代理配置完成: {proxy_config['ip']}:{proxy_config['port']}")
        else:
            logger.warning(f"[会话{session_id}] 未能获取代理IP，使用直连")
        
        # 记录开始连接时间
        connection_start_time = time.time()
        logger.info(f"[会话{session_id}] 开始连接到 Selenium Grid...")
        
        # 初始化
        taobao_business.initialize()
        taobao_business.initialize_pages()

        # 计算连接时间
        connection_time = time.time() - connection_start_time
        logger.info(f"连接成功！web session : {taobao_business.get_driver().session_id}  连接耗时: {connection_time:.3f} 秒")
        
        # 记录浏览器开始时间
        browser_start_time = time.time()
        
        
        # 执行图片搜索流程
        success, product_titles = taobao_business.execute_image_search_with_actions(full_image_path)
        product_count = len(product_titles) if product_titles else 0
        
        # 计算浏览器时间
        browser_time = time.time() - browser_start_time
        logger.info(f"[会话{session_id}] 淘宝网站访问完成！访问耗时: {browser_time:.3f} 秒")
        
        # 计算总时间
        total_time = connection_time + browser_time
        end_time = datetime.now()
        
        logger.info(f"[会话{session_id}] 时间统计 - 连接: {connection_time:.3f}s, 浏览器: {browser_time:.3f}s, 总计: {total_time:.3f}s")
        
        # 构建响应
        message = f"淘宝搜索{'成功' if success else '失败'} - 连接: {connection_time:.3f}s, 浏览器: {browser_time:.3f}s"
        
        taobao_business.get_driver().save_screenshot(screenshot_path)

        return TaobaoSearchResponse(
            success=success,
            uid=uid,
            connection_time=round(connection_time, 3),
            browser_time=round(browser_time, 3),
            total_time=round(total_time, 3),
            image_path=image_path,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            error=None if success else "搜索业务执行失败",
            message=message,
            screen_shot_url=screen_shot_url,
            product_titles=product_titles if success else None,
            product_count=product_count
        )
        
    except Exception as e:
        error_msg = f"淘宝搜索执行失败: {str(e)}"
        end_time = datetime.now()
        logger.error(f"[会话{session_id}] {error_msg}")
        try:
            if 'taobao_business' in locals() and taobao_business:
                taobao_business.get_driver().save_screenshot(screenshot_path)
        except:
            pass
    
        return TaobaoSearchResponse(
            success=False,
            uid=uid,
            connection_time=0.0,
            browser_time=0.0,
            total_time=(end_time - start_time).total_seconds(),
            image_path=image_path,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            error=str(e),
            message=error_msg,
            screen_shot_url=None,
            product_titles=None,
            product_count=0
        )
        
    finally:
        # 清理资源
        try:
            if 'taobao_business' in locals() and taobao_business:
                # time.sleep(90)
                taobao_business.cleanup()
                logger.info(f"[会话{session_id}] 资源清理完成")
        except Exception as cleanup_error:
            logger.warning(f"[会话{session_id}] 清理资源时发生错误: {cleanup_error}")

@router.get("/search", response_model=TaobaoSearchResponse, summary="执行淘宝图片搜索")
async def taobao_search(
    uid: str,
    image_path: str = "logo.png",
    timeout: int = 120,
    proxy_provider: str = ProxyProviderNames.TIANQI
):
    """
    执行淘宝图片搜索测试（异步接口，直接返回结果）
    
    - **uid**: 用户ID（必需）
    - **image_path**: 搜索图片路径
    - **timeout**: 超时时间（秒）
    - **proxy_provider**: 代理提供者，可选值：
        - "tianqi": 天启代理（默认）
        - "juliang": 巨量代理
    """
    logger.info(f"[用户{uid}] 开始淘宝搜索请求，使用代理: {proxy_provider}")
    
    # 使用线程池执行同步任务，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # 使用默认线程池
        sync_taobao_search_task,
        uid,
        image_path,
        timeout,
        proxy_provider
    )
    
    logger.info(f"[用户{uid}] 淘宝搜索请求完成")
    return result


@router.get("/health", summary="健康检查")
def health_check():
    """API健康检查"""
    return {
        "status": "healthy",
        "service": "淘宝搜索测试 API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
