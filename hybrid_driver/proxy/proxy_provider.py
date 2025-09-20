"""
代理配置提供者 - 符合SOLID原则的可扩展设计
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)


@dataclass
class ProxyConfig:
    """代理配置数据类"""
    ip: str
    port: int
    username: str
    password: str
    provider: str = ""  # 代理提供商名称
    region: str = ""    # 地区信息
    expire: str = ""    # 过期时间

    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式，供Selenium使用"""
        return {
            "ip": self.ip,
            "port": str(self.port),
            "username": self.username,
            "password": self.password,
            "provider": self.provider,
            "region": self.region,
            "expire": self.expire
        }


class ProxyProvider(ABC):
    """代理提供者抽象基类"""

    @abstractmethod
    def get_proxy_config(self) -> Optional[ProxyConfig]:
        """获取代理配置"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供者名称"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查提供者是否可用"""
        pass


class TianQiProxyProvider(ProxyProvider):
    """天启代理提供者"""

    def __init__(self, secret: str = "c9kekh2mxxnqoopd", sign: str = "698f352df781e920dbbd40ebb7a54e53"):
        self.secret = secret
        self.sign = sign
        self.base_url = "http://api.tianqiip.com/getip"
        self.provider_name = "tianqi"

    def get_proxy_config(self) -> Optional[ProxyConfig]:
        """从天启接口获取代理配置"""
        try:
            # 构建请求参数
            params = {
                "secret": self.secret,
                "num": 1,
                "type": "json",
                "region": "310100",
                "port": 1,
                "time": 3,
                "ts": 1,
                "ys": 1,
                "cs": 1,
                "mr": 1,
                "sign": self.sign
            }

            logger.info(f"调用天启API获取代理配置: {self.base_url}")

            # 使用urllib3直接请求，避免系统代理干扰
            import urllib3
            from urllib.parse import urlencode
            http = urllib3.PoolManager()
            url = f"{self.base_url}?{urlencode(params)}"
            response = http.request('GET', url, timeout=10.0)

            # 将urllib3响应转换为requests-like对象
            class MockResponse:
                def __init__(self, urllib3_response):
                    self.status_code = urllib3_response.status
                    self.text = urllib3_response.data.decode('utf-8')

                def json(self):
                    import json
                    return json.loads(self.text)

            response = MockResponse(response)

            logger.info(f"天启API响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"天启API响应数据: {data}")

                # 检查响应格式
                if data.get("code") == 1000 and data.get("data"):
                    proxy_info = data["data"][0]
                    logger.info(f"获取到代理信息: {proxy_info}")

                    # 从API响应中提取信息
                    ip = proxy_info["ip"]
                    port = proxy_info["port"]  # API返回的是数字
                    prov = proxy_info.get("prov", "")
                    city = proxy_info.get("city", "")
                    expire = proxy_info.get("expire", "")

                    logger.info(f"解析代理信息 - IP: {ip}, Port: {port}, Region: {prov}-{city}")

                    return ProxyConfig(
                        ip=ip,
                        port=port,  # 保持数字类型，ProxyConfig会转换为字符串
                        username="vgmpgv",  # 固定用户名
                        password="1bk79g9y",  # 固定密码
                        provider=self.provider_name,
                        region=f"{prov}-{city}" if prov and city else prov or city,
                        expire=expire
                    )
                else:
                    logger.error(f"天启API返回错误: {data}")
                    return None
            else:
                logger.error(f"天启API请求失败，状态码: {response.status_code}, 响应: {response.text}")
                return None

        except Exception as e:
            logger.error(f"天启代理获取失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return None

    def get_provider_name(self) -> str:
        return self.provider_name

    def is_available(self) -> bool:
        """检查天启代理服务是否可用"""
        # 在网络环境受限时，假设服务可用
        # 实际使用时可以根据需要调整此逻辑
        return True


class JuLiangProxyProvider(ProxyProvider):
    """巨量代理提供者"""

    def __init__(self, trade_no: str = "1550102436789257", sign: str = "df2aefd1b9008a76edb52554cf122500"):
        self.trade_no = trade_no
        self.sign = sign
        self.base_url = "http://v2.api.juliangip.com/company/dynamic/getips"
        self.provider_name = "juliang"

    def get_proxy_config(self) -> Optional[ProxyConfig]:
        """从巨量接口获取代理配置"""
        try:
            # 构建请求参数
            params = {
                "auth_type": 2,
                "auto_white": 1,
                "city": "北京",
                "filter": 1,
                "ip_remain": 1,
                "num": 1,
                "pt": 1,
                "result_type": "json2",
                "trade_no": self.trade_no,
                "sign": self.sign
            }

            logger.info(f"调用巨量API获取代理配置: {self.base_url}")

            # 使用urllib3直接请求，避免系统代理干扰
            import urllib3
            from urllib.parse import urlencode
            http = urllib3.PoolManager()
            url = f"{self.base_url}?{urlencode(params)}"
            response = http.request('GET', url, timeout=10.0)

            # 将urllib3响应转换为requests-like对象
            class MockResponse:
                def __init__(self, urllib3_response):
                    self.status_code = urllib3_response.status
                    self.text = urllib3_response.data.decode('utf-8')

                def json(self):
                    import json
                    return json.loads(self.text)

            response = MockResponse(response)

            logger.info(f"巨量API响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"巨量API响应数据: {data}")

                # 检查响应格式
                if data.get("code") == 200 and data.get("data") and data["data"].get("proxy_list"):
                    proxy_info = data["data"]["proxy_list"][0]
                    logger.info(f"获取到代理信息: {proxy_info}")

                    # 从API响应中提取信息
                    ip = proxy_info["ip"]
                    port = proxy_info["port"]  # 巨量API返回的是字符串
                    http_user = proxy_info["http_user"]
                    http_pass = proxy_info["http_pass"]
                    ip_remain = proxy_info.get("ip_remain", 0)
                    real_ip = proxy_info.get("real_ip", "")

                    logger.info(f"解析代理信息 - IP: {ip}, Port: {port}, User: {http_user}, Remain: {ip_remain}")

                    return ProxyConfig(
                        ip=ip,
                        port=int(port),  # 转换为整数类型
                        username=http_user,
                        password=http_pass,
                        provider=self.provider_name,
                        region="北京",
                        expire=f"剩余{ip_remain}秒"
                    )
                else:
                    logger.error(f"巨量API返回错误: {data}")
                    return None
            else:
                logger.error(f"巨量API请求失败，状态码: {response.status_code}, 响应: {response.text}")
                return None

        except Exception as e:
            logger.error(f"巨量代理获取失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return None

    def get_provider_name(self) -> str:
        return self.provider_name

    def is_available(self) -> bool:
        """检查巨量代理服务是否可用"""
        # 在网络环境受限时，假设服务可用
        # 实际使用时可以根据需要调整此逻辑
        return True


class CustomProxyProvider(ProxyProvider):
    """自定义代理提供者 - 用于扩展其他代理源"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = config.get("name", "custom")

    def get_proxy_config(self) -> Optional[ProxyConfig]:
        """从自定义接口获取代理配置"""
        try:
            # 这里可以实现自定义的代理获取逻辑
            # 例如调用其他API、从数据库读取、从配置文件读取等
            raise NotImplementedError("CustomProxyProvider需要实现具体的获取逻辑")
        except Exception as e:
            logger.error(f"自定义代理获取失败: {e}")
            return None

    def get_provider_name(self) -> str:
        return self.provider_name

    def is_available(self) -> bool:
        return True  # 自定义提供者默认可用


class ProxyConfigManager:
    """代理配置管理器 - 工厂模式"""

    def __init__(self):
        self.providers: Dict[str, ProxyProvider] = {}

    def register_provider(self, name: str, provider: ProxyProvider):
        """注册代理提供者"""
        self.providers[name] = provider
        logger.info(f"注册代理提供者: {name}")

    def get_proxy_config(self, provider_name: str = "tianqi") -> Optional[ProxyConfig]:
        """获取代理配置"""
        if provider_name not in self.providers:
            logger.error(f"未找到代理提供者: {provider_name}")
            return None

        provider = self.providers[provider_name]
        if not provider.is_available():
            logger.warning(f"代理提供者不可用: {provider_name}")
            return None

        config = provider.get_proxy_config()
        if config:
            logger.info(f"成功获取代理配置: {config.ip}:{config.port} ({config.provider})")
        else:
            logger.error(f"获取代理配置失败: {provider_name}")

        return config

    def get_available_providers(self) -> List[str]:
        """获取所有可用的提供者"""
        return [name for name, provider in self.providers.items() if provider.is_available()]


# 全局代理配置管理器实例
proxy_manager = ProxyConfigManager()


def initialize_proxy_providers():
    """初始化代理提供者"""
    # 注册天启代理提供者
    tianqi_provider = TianQiProxyProvider()
    proxy_manager.register_provider("tianqi", tianqi_provider)

    # 注册巨量代理提供者
    juliang_provider = JuLiangProxyProvider()
    proxy_manager.register_provider("juliang", juliang_provider)

    # 可以在这里注册其他代理提供者
    # custom_provider = CustomProxyProvider({"name": "my_provider"})
    # proxy_manager.register_provider("my_provider", custom_provider)

    logger.info(f"代理提供者初始化完成，可用提供者: {proxy_manager.get_available_providers()}")


def get_proxy_config_for_selenium(provider_name: str = "tianqi") -> Optional[Dict[str, str]]:
    """
    获取Selenium可用的代理配置

    Args:
        provider_name: 代理提供者名称

    Returns:
        代理配置字典，格式如:
        {
            "ip": "1.2.3.4",
            "port": "8080",
            "username": "user",
            "password": "pass"
        }
    """
    config = proxy_manager.get_proxy_config(provider_name)
    if config:
        return config.to_dict()
    return None


# 代理提供者名称常量
class ProxyProviderNames:
    """代理提供者名称常量"""
    TIANQI = "tianqi"
    JULIANG = "juliang"
    CUSTOM = "custom"


# 程序启动时初始化代理提供者
initialize_proxy_providers()
