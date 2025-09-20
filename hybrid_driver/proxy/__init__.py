"""
代理配置系统模块
提供可扩展的代理配置获取和管理功能
"""

from .proxy_provider import (
    ProxyConfig,
    ProxyProvider,
    TianQiProxyProvider,
    JuLiangProxyProvider,
    CustomProxyProvider,
    ProxyConfigManager,
    ProxyProviderNames,
    proxy_manager,
    initialize_proxy_providers,
    get_proxy_config_for_selenium
)

__all__ = [
    'ProxyConfig',
    'ProxyProvider',
    'TianQiProxyProvider',
    'JuLiangProxyProvider',
    'CustomProxyProvider',
    'ProxyConfigManager',
    'ProxyProviderNames',
    'proxy_manager',
    'initialize_proxy_providers',
    'get_proxy_config_for_selenium'
]

# 模块版本信息
__version__ = "1.0.0"
