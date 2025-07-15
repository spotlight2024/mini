"""
API配置管理
"""
from typing import Dict, Any
from pydantic import BaseModel


class APIConfig(BaseModel):
    """API配置类"""
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # 应用配置
    title: str = "SpotLight Hybrid Driver API"
    description: str = "混合驱动自动化测试API服务"
    version: str = "1.0.0"
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 超时配置
    default_timeout: int = 10
    connection_timeout: int = 30
    
    # 错误码配置
    error_codes: Dict[str, int] = {
        "SUCCESS": 0,
        "DEVICE_NOT_FOUND": 1002,
        "ELEMENT_NOT_FOUND": 1003,
        "WEBDRIVER_NOT_INITIALIZED": 1004,
        "NO_AVAILABLE_PAGES": 1006,
        "PAGE_SWITCH_FAILED": 1007,
        "ELEMENT_NOT_INTERACTABLE": 1009,
        "OPERATION_TIMEOUT": 1010,
        "SYSTEM_EXCEPTION": 2000,
    }
    
    # 页面类型配置
    page_types: Dict[str, Dict[str, Any]] = {
        "Home": {
            "keywords": ["首页", "主页", "home", "menu_page"],
            "url_patterns": ["home", "index"]
        },
        "ShopDetail": {
            "keywords": ["店铺", "商店", "shop", "store", "商品"],
            "url_patterns": ["shop", "store"]
        },
        "SearchShopList": {
            "keywords": ["搜索", "search", "店铺列表"],
            "url_patterns": ["search"]
        }
    }
    
    class Config:
        env_file = ".env"
        env_prefix = "API_"


# 全局配置实例
config = APIConfig() 