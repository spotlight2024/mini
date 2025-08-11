"""应用程序配置文件"""

from typing import Dict, Any
import os


class Config:
    """应用程序配置类"""

    # HTTP请求配置
    HTTP_TIMEOUT: int = int(os.getenv("PS_HTTP_TIMEOUT", "120"))
    HTTP_MAX_RETRIES: int = int(os.getenv("PS_HTTP_MAX_RETRIES", "3"))

    # 网络配置
    SKIP_NETWORK_CHECK: bool = os.getenv("PS_SKIP_NETWORK_CHECK", "false").lower() == "true"
    FALLBACK_IP: str = os.getenv("PS_FALLBACK_IP", "127.0.0.1")

    # 沙盒配置
    SANDBOX_TIMEOUT: int = int(os.getenv("PS_SANDBOX_TIMEOUT", "300"))
    ENABLE_SANDBOX_LOGGING: bool = os.getenv("PS_ENABLE_SANDBOX_LOGGING", "true").lower() == "true"

    # 日志配置
    LOG_LEVEL: str = os.getenv("PS_LOG_LEVEL", "INFO")
    ENABLE_REQUEST_LOGGING: bool = os.getenv("PS_ENABLE_REQUEST_LOGGING", "true").lower() == "true"

    # 编码配置
    ENCODING_SPECIAL_CHARS: set = {' ', '\n', '\r', '\t', '#', '=', ',', '|', '-', '[', ']', '{', '}'}

    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置项"""
        return {
            "HTTP_TIMEOUT": cls.HTTP_TIMEOUT,
            "HTTP_MAX_RETRIES": cls.HTTP_MAX_RETRIES,
            "SKIP_NETWORK_CHECK": cls.SKIP_NETWORK_CHECK,
            "FALLBACK_IP": cls.FALLBACK_IP,
            "SANDBOX_TIMEOUT": cls.SANDBOX_TIMEOUT,
            "ENABLE_SANDBOX_LOGGING": cls.ENABLE_SANDBOX_LOGGING,
            "LOG_LEVEL": cls.LOG_LEVEL,
            "ENABLE_REQUEST_LOGGING": cls.ENABLE_REQUEST_LOGGING,
        }

    @classmethod
    def print_config(cls):
        """打印当前配置"""
        print("[CONFIG] Current configuration:")
        for key, value in cls.get_all_config().items():
            print(f"[CONFIG] {key}: {value}")