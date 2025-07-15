import uuid
import logging
from typing import Optional


def gen_trace_id() -> str:
    """生成追踪ID"""
    return str(uuid.uuid4())


def check_page_type(url: str, page_source: str, required_page: str) -> bool:
    """检查页面类型"""
    try:
        # 根据URL和页面内容判断页面类型
        if required_page == "Home":
            # 检查是否为首页
            if "home" in url.lower() or "index" in url.lower():
                return True
            # 检查页面源码中是否包含首页特征
            if any(keyword in page_source.lower() for keyword in ["首页", "主页", "home", "menu_page"]):
                return True
        
        elif required_page == "ShopDetail":
            # 检查是否为店铺详情页
            if "shop" in url.lower() or "store" in url.lower():
                return True
            # 检查页面源码中是否包含店铺详情页特征
            if any(keyword in page_source.lower() for keyword in ["店铺", "商店", "shop", "store", "商品"]):
                return True
        
        elif required_page == "SearchShopList":
            # 检查是否为店铺搜索页
            if "search" in url.lower():
                return True
            if any(keyword in page_source.lower() for keyword in ["搜索", "search", "店铺列表"]):
                return True
        
        # 更多页面类型可以在此扩展
        
        return False
        
    except Exception as e:
        logging.error(f"Page type check failed: {str(e)}")
        return False


def detect_current_page(url: str, page_source: str) -> str:
    """检测当前页面类型"""
    try:
        # 根据URL和页面内容检测当前页面
        if "home" in url.lower() or "index" in url.lower():
            return "Home"
        elif "shop" in url.lower() or "store" in url.lower():
            return "ShopDetail"
        elif "search" in url.lower():
            return "SearchShopList"
        
        # 根据页面内容检测
        if any(keyword in page_source.lower() for keyword in ["首页", "主页", "menu_page"]):
            return "Home"
        elif any(keyword in page_source.lower() for keyword in ["店铺", "商店", "商品列表"]):
            return "ShopDetail"
        elif any(keyword in page_source.lower() for keyword in ["搜索", "店铺列表"]):
            return "SearchShopList"
        
        return "Unknown"
        
    except Exception as e:
        logging.error(f"Page detection failed: {str(e)}")
        return "Unknown" 