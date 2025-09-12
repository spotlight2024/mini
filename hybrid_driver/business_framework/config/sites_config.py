"""
网站配置 - 定义各种网站的配置信息
"""
from typing import Dict, Any


class SitesConfig:
    """网站配置类"""
    
    # 淘宝配置
    TAOBAO = {
        'site_name': 'taobao',
        'home_url': 'https://www.taobao.com/',
        'hub_url': 'http://172.16.1.129:30444/wd/hub',
        'timeout': 30,
        'implicit_wait': 10,
        'page_load_timeout': 30,
        'webdriver_mode': 'remote',
        'browser_version': '138',
        'platform_name': 'linux',
        'android_package': 'com.tencent.mm',
        'android_process': 'com.tencent.mm:appbrand0'
    }
    
    # 京东配置
    JD = {
        'site_name': 'jd',
        'home_url': 'https://www.jd.com/',
        'hub_url': 'http://172.16.1.129:30444/wd/hub',
        'timeout': 30,
        'implicit_wait': 10,
        'page_load_timeout': 30,
        'webdriver_mode': 'remote',
        'browser_version': '138',
        'platform_name': 'linux',
        'android_package': 'com.tencent.mm',
        'android_process': 'com.tencent.mm:appbrand0'
    }
    
    # 其他网站配置
    OTHER_SITE = {
        'site_name': 'other',
        'home_url': 'https://www.example.com/',
        'hub_url': 'http://172.16.1.129:30444/wd/hub',
        'timeout': 30,
        'implicit_wait': 10,
        'page_load_timeout': 30,
        'webdriver_mode': 'remote',
        'browser_version': '138',
        'platform_name': 'linux',
        'android_package': 'com.tencent.mm',
        'android_process': 'com.tencent.mm:appbrand0'
    }
    
    @classmethod
    def get_site_config(cls, site_name: str) -> Dict[str, Any]:
        """获取网站配置"""
        configs = {
            'taobao': cls.TAOBAO,
            'jd': cls.JD,
            'other': cls.OTHER_SITE
        }
        return configs.get(site_name, cls.OTHER_SITE)
    
    @classmethod
    def get_available_sites(cls) -> list:
        """获取可用的网站列表"""
        return ['taobao', 'jd', 'other']
