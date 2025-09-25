#!/usr/bin/env python3
"""
淘宝搜索测试 API - 优化版本
包含性能优化、架构改进、错误处理增强等特性
"""
import asyncio
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from functools import lru_cache
from typing import Dict, Any, Optional, List, Union, Literal
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator

from hybrid_driver.business_framework.business import taobao_business
from hybrid_driver.business_framework.business.taobao_business import TaobaoBusiness
from hybrid_driver.log_config import get_logger
from hybrid_driver.proxy.proxy_provider import get_proxy_config_for_selenium, ProxyProviderNames
from hybrid_driver.config.settings import Settings

# 创建路由器
router = APIRouter(prefix="/test/taobao", tags=["淘宝搜索测试"])
logger = get_logger(__name__)

# ==================== 类型定义 ====================

class ProxyProviderType(str, Enum):
    """代理提供者类型枚举"""
    TIANQI = "tianqi"
    JULIANG = "juliang"
    KUAI = "kuai"
    CUSTOM = "custom"

class SearchStatus(str, Enum):
    """搜索状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    connection_time: float = 0.0
    browser_time: float = 0.0
    total_time: float = 0.0
    memory_usage_mb: float = 0.0
    proxy_fetch_time: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "connection_time": round(self.connection_time, 3),
            "browser_time": round(self.browser_time, 3),
            "total_time": round(self.total_time, 3),
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "proxy_fetch_time": round(self.proxy_fetch_time, 3)
        }

# ==================== Pydantic 模型 ====================

class HumanActionsSettings(BaseModel):
    """人类化行为配置"""

    min_steps: Optional[int] = Field(default=None, description="最小轨迹分段数")
    max_steps: Optional[int] = Field(default=None, description="最大轨迹分段数")
    min_step_duration_ms: Optional[int] = Field(default=None, description="单段最小持续时间(ms)")
    max_step_duration_ms: Optional[int] = Field(default=None, description="单段最大持续时间(ms)")
    min_pause: Optional[float] = Field(default=None, description="段间最小停顿(秒)")
    max_pause: Optional[float] = Field(default=None, description="段间最大停顿(秒)")
    path_jitter: Optional[float] = Field(default=None, description="轨迹抖动幅度")
    target_jitter: Optional[float] = Field(default=None, description="落点随机抖动")
    overshoot_chance: Optional[float] = Field(default=None, description="过冲概率")
    overshoot_range: Optional[List[float]] = Field(default=None, description="过冲距离范围")
    seed: Optional[int] = Field(default=None, description="随机种子")


class TaobaoSearchRequest(BaseModel):
    """淘宝搜索请求模型"""
    uid: str = Field(..., description="用户ID", min_length=1, max_length=100)
    image_path: str = Field(default="logo.png", description="搜索图片路径")
    timeout: int = Field(default=120, description="超时时间（秒）", ge=10, le=600)
    proxy_provider: ProxyProviderType = Field(default=ProxyProviderType.TIANQI, description="代理提供者")
    enable_cache: bool = Field(default=False, description="是否启用缓存（已禁用代理缓存）")
    max_retries: int = Field(default=3, description="最大重试次数", ge=0, le=10)
    human_actions: Optional[HumanActionsSettings] = Field(
        default=None,
        description="人类化行为配置（不传则保持默认快速模式）",
    )
    
    @validator('image_path')
    def validate_image_path(cls, v):
        """验证图片路径"""
        if not v.strip():
            raise ValueError("图片路径不能为空")
        return v.strip()

class TaobaoSearchResponse(BaseModel):
    """淘宝搜索响应模型"""
    success: bool = Field(description="是否成功")
    status: SearchStatus = Field(description="搜索状态")
    uid: str = Field(description="用户ID")
    session_id: str = Field(description="会话ID")
    performance_metrics: Dict[str, float] = Field(description="性能指标")
    image_path: str = Field(description="搜索图片路径")
    start_time: str = Field(description="开始时间")
    end_time: str = Field(description="结束时间")
    error: Optional[str] = Field(default=None, description="错误信息")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    message: str = Field(description="执行消息")
    screen_shot_url: Optional[str] = Field(default=None, description="截图文件URL路径")
    product_titles: Optional[List[str]] = Field(default=None, description="商品标题列表")
    product_count: int = Field(default=0, description="商品数量")
    retry_count: int = Field(default=0, description="重试次数")
    proxy_info: Optional[Dict[str, Any]] = Field(default=None, description="代理信息")

# ==================== 异常定义 ====================

class TaobaoSearchError(Exception):
    """淘宝搜索基础异常"""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

class ImageNotFoundError(TaobaoSearchError):
    """图片未找到异常"""
    def __init__(self, image_path: str):
        super().__init__(f"图片文件不存在: {image_path}", "IMAGE_NOT_FOUND")

class WebDriverConnectionError(TaobaoSearchError):
    """WebDriver连接异常"""
    def __init__(self, message: str):
        super().__init__(f"WebDriver连接失败: {message}", "WEBDRIVER_CONNECTION_ERROR")

class SearchTimeoutError(TaobaoSearchError):
    """搜索超时异常"""
    def __init__(self, timeout: int):
        super().__init__(f"搜索超时: {timeout}秒", "SEARCH_TIMEOUT")

# ==================== 服务层 ====================

class TaobaoSearchService:
    """淘宝搜索服务类 - 封装业务逻辑"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(f"{self.__class__.__name__}")
        
    @lru_cache(maxsize=100)
    def _get_image_full_path(self, image_path: str) -> str:
        """获取图片完整路径（带缓存）"""
        if os.path.isabs(image_path):
            return image_path
            
        # 从api/test目录查找test_img目录
        api_dir = os.path.dirname(os.path.abspath(__file__))
        test_img_dir = os.path.join(api_dir, "test_img")
        return os.path.join(test_img_dir, image_path)
    
    async def _get_proxy_config_fresh(self, proxy_provider: str) -> Optional[Dict[str, Any]]:
        """获取代理配置（每次都获取最新）"""
        start_time = time.time()
        try:
            # 在线程池中执行同步代理获取
            loop = asyncio.get_event_loop()
            config = await loop.run_in_executor(
                None, get_proxy_config_for_selenium, proxy_provider
            )
            
            fetch_time = time.time() - start_time
            self.logger.info(f"代理配置获取耗时: {fetch_time:.3f}秒，IP: {config.get('ip', 'N/A') if config else 'N/A'}")
            
            return config
            
        except Exception as e:
            self.logger.error(f"获取代理配置失败: {e}")
            return None
    
    def _create_business_instance(
        self,
        session_id: str,
        user_id: str,
        site_overrides: Optional[Dict[str, Any]] = None,
    ) -> TaobaoBusiness:
        """创建业务实例"""
        return TaobaoBusiness(session_id, user_id, site_overrides=site_overrides)
    
    async def _execute_search_with_timeout(self, business: TaobaoBusiness, 
                                         image_path: str, timeout: int) -> tuple[bool, List[str]]:
        """执行搜索（带超时控制）"""
        try:
            # 使用asyncio.wait_for实现超时控制
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, business.execute_image_search_with_actions, image_path
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise SearchTimeoutError(timeout)
    
    async def execute_search(self, request: TaobaoSearchRequest) -> TaobaoSearchResponse:
        """执行淘宝搜索（主要业务逻辑）"""
        uid = request.uid
        session_id = f"{request.uid}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        metrics = PerformanceMetrics()
        
        # 创建日志上下文
        log_context = f"[会话{session_id}]"
        self.logger.info(f"{log_context} 开始执行淘宝搜索任务")
        
        try:
            # 1. 验证图片文件
            full_image_path = self._get_image_full_path(request.image_path)
            if not os.path.exists(full_image_path):
                raise ImageNotFoundError(full_image_path)
            
            # 2. 获取代理配置（每次都获取最新）
            proxy_start = time.time()
            proxy_config = await self._get_proxy_config_fresh(request.proxy_provider.value)
            metrics.proxy_fetch_time = time.time() - proxy_start
            
            # 3. 创建业务实例
            if request.human_actions:
                human_action_settings = request.human_actions.model_dump(exclude_none=True)
                human_action_settings["enabled"] = True
                site_overrides = {"human_actions": human_action_settings}
                self.logger.info(f"{log_context} 人类化行为配置: {human_action_settings}")
            else:
                human_action_settings = None
                site_overrides = None
                self.logger.info(f"{log_context} 人类化行为配置: 默认模式")

            business = self._create_business_instance(session_id, uid, site_overrides)
            
            # 4. 配置代理
            if proxy_config:
                chrome_options = business.get_chrome_options()
                chrome_options.set_capability("se:proxyConfig", proxy_config)
                self.logger.info(f"{log_context} 代理配置完成: {proxy_config['ip']}:{proxy_config['port']}")
            else:
                self.logger.warning(f"{log_context} 未能获取代理IP，使用直连")
            
            # 5. 建立WebDriver连接
            connection_start = time.time()
            business.initialize()
            business.initialize_pages()
            metrics.connection_time = time.time() - connection_start
            
            web_session_id = business.get_driver().session_id
            self.logger.info(f"{log_context} 连接成功！web session: {web_session_id}, 连接耗时: {metrics.connection_time:.3f}秒")
            
            # 6. 执行搜索业务
            browser_start = time.time()
            success, product_titles = await self._execute_search_with_timeout(
                business, full_image_path, request.timeout
            )
            metrics.browser_time = time.time() - browser_start
            
            # 7. 计算总时间
            end_time = datetime.now()
            metrics.total_time = metrics.connection_time + metrics.browser_time
            
            # 8. 保存截图
            screenshot_url = await self._save_screenshot(business, session_id, uid)

            
            # 9. 构建成功响应
            return TaobaoSearchResponse(
                success=success,
                status=SearchStatus.SUCCESS if success else SearchStatus.FAILED,
                uid=request.uid,
                session_id=session_id,
                performance_metrics=metrics.to_dict(),
                image_path=request.image_path,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                message=f"淘宝搜索{'成功' if success else '失败'} - 连接: {metrics.connection_time:.3f}s, 浏览器: {metrics.browser_time:.3f}s",
                screen_shot_url=screenshot_url,
                product_titles=product_titles if success else None,
                product_count=len(product_titles) if product_titles else 0,
                proxy_info={
                    "provider": request.proxy_provider.value,
                    "ip": proxy_config.get("ip") if proxy_config else None,
                    "port": proxy_config.get("port") if proxy_config else None
                } if proxy_config else None
            )
            
        except (ImageNotFoundError, WebDriverConnectionError, SearchTimeoutError) as e:
            # 已知异常，直接处理
            return self._create_error_response(
                request, session_id, start_time, e.error_code, str(e), metrics
            )
            
        except Exception as selenium_e:
            # Selenium相关异常（从业务层传播上来的）
            if any(keyword in str(selenium_e).lower() for keyword in ['timeout', 'renderer', 'webdriver', 'session']):
                self.logger.error(f"{log_context} Selenium异常: {selenium_e}", exc_info=True)
                return self._create_error_response(
                    request, session_id, start_time, "SELENIUM_ERROR", str(selenium_e), metrics
                )
            
        except Exception as e:
            # 未知异常，记录详细信息
            self.logger.error(f"{log_context} 未知错误: {e}", exc_info=True)
            return self._create_error_response(
                request, session_id, start_time, "UNKNOWN_ERROR", str(e), metrics
            )
            
        finally:
            # 资源清理
            await self._cleanup_resources(business if 'business' in locals() else None, log_context)
    
    async def _save_screenshot(self, business: TaobaoBusiness, session_id: str, uid: str) -> Optional[str]:
        """保存截图（按uid分类）"""
        try:
            screenshot_filename = f"screenshot_{session_id}_{uuid.uuid4().hex[:8]}.png"
            
            # 按uid创建分类目录
            category_dir = f"/app/@web_screenshot/category/{uid}"
            os.makedirs(category_dir, exist_ok=True)
            screenshot_path = os.path.join(category_dir, screenshot_filename)
            
            # 在线程池中执行截图保存
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, business.get_driver().save_screenshot, screenshot_path
            )
            
            return f"/@web_screenshot/category/{uid}/{screenshot_filename}"
        except Exception as e:
            self.logger.warning(f"保存截图失败: {e}")
            return None
    
    def _create_error_response(self, request: TaobaoSearchRequest, session_id: str,
                             start_time: datetime, error_code: str, error_message: str,
                             metrics: PerformanceMetrics) -> TaobaoSearchResponse:
        """创建错误响应"""
        end_time = datetime.now()
        return TaobaoSearchResponse(
            success=False,
            status=SearchStatus.TIMEOUT if error_code == "SEARCH_TIMEOUT" else SearchStatus.ERROR,
            uid=request.uid,
            session_id=session_id,
            performance_metrics=metrics.to_dict(),
            image_path=request.image_path,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            error=error_message,
            error_code=error_code,
            message=f"淘宝搜索失败: {error_message}",
            product_count=0
        )
    
    async def _cleanup_resources(self, business: Optional[TaobaoBusiness], log_context: str):
        """异步资源清理"""
        if business:
            try:
                # 在线程池中执行清理
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, business.cleanup)
                self.logger.info(f"{log_context} 资源清理完成")
            except Exception as e:
                self.logger.warning(f"{log_context} 清理资源时发生错误: {e}")

# ==================== 依赖注入 ====================

@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例）"""
    return Settings()

def get_search_service(settings: Settings = Depends(get_settings)) -> TaobaoSearchService:
    """获取搜索服务实例"""
    return TaobaoSearchService(settings)

# ==================== API 路由 ====================

@router.post("/search", response_model=TaobaoSearchResponse, summary="执行淘宝图片搜索（优化版）")
async def taobao_search_optimized(
    request: TaobaoSearchRequest,
    service: TaobaoSearchService = Depends(get_search_service)
):
    """
    执行淘宝图片搜索测试（优化版本）
    
    优化特性：
    - ✅ 类型安全的请求验证
    - ✅ 异步资源管理
    - ✅ 每次获取最新代理IP
    - ✅ 超时控制
    - ✅ 详细的错误分类
    - ✅ 性能指标监控
    - ✅ 依赖注入架构
    """
    logger.info(f"[用户{request.uid}] 开始淘宝搜索请求，使用代理: {request.proxy_provider.value}")
    
    try:
        result = await service.execute_search(request)
        logger.info(f"[用户{request.uid}] 淘宝搜索请求完成，状态: {result.status}")
        return result
        
    except Exception as e:
        logger.error(f"[用户{request.uid}] API层异常: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务内部错误: {str(e)}")

# 保持向后兼容的旧接口
@router.get("/search", response_model=TaobaoSearchResponse, summary="执行淘宝图片搜索（兼容版）")
async def taobao_search_legacy(
    uid: str,
    image_path: str = "logo.png",
    timeout: int = 120,
    proxy_provider: str = ProxyProviderNames.TIANQI,
    service: TaobaoSearchService = Depends(get_search_service)
):
    """
    执行淘宝图片搜索测试（向后兼容接口）
    
    为了保持与现有系统的兼容性而保留的接口
    """
    # 转换为新的请求模型
    try:
        provider_enum = ProxyProviderType(proxy_provider)
    except ValueError:
        provider_enum = ProxyProviderType.TIANQI
    
    request = TaobaoSearchRequest(
        uid=uid,
        image_path=image_path,
        timeout=timeout,
        proxy_provider=provider_enum
    )
    
    return await taobao_search_optimized(request, service)

@router.get("/health", summary="健康检查")
def health_check():
    """API健康检查"""
    return {
        "status": "healthy",
        "service": "淘宝搜索测试 API（优化版）",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": [
            "类型安全",
            "异步处理", 
            "代理缓存",
            "超时控制",
            "性能监控",
            "错误分类",
            "依赖注入"
        ]
    }

@router.get("/metrics", summary="性能指标")
async def get_metrics(service: TaobaoSearchService = Depends(get_search_service)):
    """获取性能指标"""
    return {
        "proxy_fetch_mode": "fresh",  # 每次都获取最新代理
        "cache_enabled": False,
        "timestamp": datetime.now().isoformat()
    }
