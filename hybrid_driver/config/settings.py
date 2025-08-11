"""
应用配置管理
统一管理所有配置项，包括API配置、WebDriver配置、设备池配置等
支持从环境变量、配置文件、默认值等多种方式读取配置
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# 加载环境变量文件
load_dotenv()


class Settings:
    """应用配置管理类"""

    # ==================== API服务配置 ====================
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "10001"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    API_WORKERS: int = int(os.getenv("API_WORKERS", "1"))
    API_TITLE: str = os.getenv("API_TITLE", "SpotLight Hybrid Driver API")
    API_DESCRIPTION: str = os.getenv("API_DESCRIPTION", "混合驱动自动化测试API服务")
    API_VERSION: str = os.getenv("API_VERSION", "1.0.0")

    # ==================== 日志配置 ====================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/hybrid_driver.log")
    LOG_MAX_SIZE: str = os.getenv("LOG_MAX_SIZE", "10MB")
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    LOG_ENABLE_CONSOLE: bool = os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true"
    LOG_ENABLE_FILE: bool = os.getenv("LOG_ENABLE_FILE", "true").lower() == "true"

    # ==================== WebDriver配置 ====================
    SELENIUM_TIMEOUT: int = int(os.getenv("SELENIUM_TIMEOUT", "30"))
    APPIUM_TIMEOUT: int = int(os.getenv("APPIUM_TIMEOUT", "30"))
    CHROME_DRIVER_PATH: Optional[str] = os.getenv("CHROME_DRIVER_PATH")
    CHROME_DRIVER_VERSION: Optional[str] = os.getenv("CHROME_DRIVER_VERSION")
    CHROME_DRIVER_DOWNLOAD_URL: Optional[str] = os.getenv("CHROME_DRIVER_DOWNLOAD_URL")
    APPIUM_SERVER_URL: str = os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")
    WEBDRIVER_MODE: str = os.getenv(
        "WEBDRIVER_MODE", "remote"
    )  # 可选值：'local' 或 'remote'
    REMOTE_WEBDRIVER_URL: Optional[str] = os.getenv(
        "REMOTE_WEBDRIVER_URL", "http://172.16.1.129:4444/wd/hub"
    )

    # Selenium Grid配置
    SELENIUM_HUB_HOST: str = os.getenv("SELENIUM_HUB_HOST", "selenium-hub")
    SELENIUM_HUB_PUBLISH_PORT: int = int(os.getenv("SELENIUM_HUB_PUBLISH_PORT", "4442"))
    SELENIUM_HUB_SUBSCRIBE_PORT: int = int(
        os.getenv("SELENIUM_HUB_SUBSCRIBE_PORT", "4443")
    )
    SELENIUM_NODE_COUNT: int = int(os.getenv("SELENIUM_NODE_COUNT", "2"))
    SELENIUM_NODE_MAX_SESSIONS: int = int(os.getenv("SELENIUM_NODE_MAX_SESSIONS", "4"))
    SELENIUM_NODE_SESSION_TIMEOUT: int = int(
        os.getenv("SELENIUM_NODE_SESSION_TIMEOUT", "300")
    )

    # ==================== 设备池配置 ====================
    MAX_DEVICES: int = int(os.getenv("MAX_DEVICES", "10"))
    CLEANUP_INTERVAL: int = int(os.getenv("CLEANUP_INTERVAL", "300"))
    DEVICE_TIMEOUT: int = int(os.getenv("DEVICE_TIMEOUT", "60"))
    DEVICE_CONNECTION_RETRY: int = int(os.getenv("DEVICE_CONNECTION_RETRY", "3"))
    DEVICE_CONNECTION_RETRY_DELAY: int = int(
        os.getenv("DEVICE_CONNECTION_RETRY_DELAY", "5")
    )

    # ==================== 操作配置 ====================
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "10"))
    DEFAULT_WAIT: int = int(os.getenv("DEFAULT_WAIT", "5"))
    ELEMENT_WAIT_TIMEOUT: int = int(os.getenv("ELEMENT_WAIT_TIMEOUT", "10"))
    PAGE_LOAD_TIMEOUT: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "30"))
    SCRIPT_TIMEOUT: int = int(os.getenv("SCRIPT_TIMEOUT", "30"))

    # ==================== 线程池配置 ====================
    THREAD_POOL_MAX_WORKERS: int = int(os.getenv("THREAD_POOL_MAX_WORKERS", "100"))
    THREAD_POOL_MIN_WORKERS: int = int(os.getenv("THREAD_POOL_MIN_WORKERS", "10"))

    # ==================== 连接池配置 ====================
    CONNECTION_POOL_MAX_CONNECTIONS: int = int(
        os.getenv("CONNECTION_POOL_MAX_CONNECTIONS", "3")
    )
    CONNECTION_POOL_MAX_IDLE_TIME: int = int(
        os.getenv("CONNECTION_POOL_MAX_IDLE_TIME", "300")
    )

    # ==================== 文件路径配置 ====================
    PROJECT_ROOT: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    CONFIG_DIR: str = os.path.join(PROJECT_ROOT, "config")
    LOGS_DIR: str = os.path.join(PROJECT_ROOT, "logs")
    DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
    CACHE_DIR: str = os.path.join(PROJECT_ROOT, "cache")

    # ==================== 网络配置 ====================
    NETWORK_NAME: str = os.getenv("NETWORK_NAME", "spotlight-network")
    NETWORK_TIMEOUT: int = int(os.getenv("NETWORK_TIMEOUT", "30"))

    # ==================== 证书配置 ====================
    SE_INSTALL_CERTIFICATES: bool = (
        os.getenv("SE_INSTALL_CERTIFICATES", "false").lower() == "true"
    )
    CERTIFICATES_DIR: str = os.path.join(PROJECT_ROOT, "certs")

    # ==================== 缓存配置 ====================
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))

    # ==================== 监控配置 ====================
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    METRICS_INTERVAL: int = int(os.getenv("METRICS_INTERVAL", "60"))
    AUTO_SCALE_ENABLED: bool = (
        os.getenv("AUTO_SCALE_ENABLED", "false").lower() == "true"
    )

    # ==================== 安全配置 ====================
    CORS_ENABLED: bool = os.getenv("CORS_ENABLED", "true").lower() == "true"
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    API_KEY_ENABLED: bool = os.getenv("API_KEY_ENABLED", "false").lower() == "true"
    API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "X-API-Key")

    @classmethod
    def load_from_file(cls, config_file: str = None) -> None:
        """从配置文件加载配置"""
        if config_file is None:
            config_file = os.path.join(cls.CONFIG_DIR, "config.json")

        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                # 更新配置项
                for key, value in config_data.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)

                print(f"配置已从文件加载: {config_file}")
            except Exception as e:
                print(f"加载配置文件失败: {e}")

    @classmethod
    def save_to_file(cls, config_file: str = None) -> None:
        """保存配置到文件"""
        if config_file is None:
            config_file = os.path.join(cls.CONFIG_DIR, "config.json")

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_file), exist_ok=True)

            config_data = cls.get_config()
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            print(f"配置已保存到文件: {config_file}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取所有配置项"""
        return {
            "api": {
                "host": cls.API_HOST,
                "port": cls.API_PORT,
                "reload": cls.API_RELOAD,
                "workers": cls.API_WORKERS,
                "title": cls.API_TITLE,
                "description": cls.API_DESCRIPTION,
                "version": cls.API_VERSION,
            },
            "logging": {
                "level": cls.LOG_LEVEL,
                "format": cls.LOG_FORMAT,
                "file": cls.LOG_FILE,
                "max_size": cls.LOG_MAX_SIZE,
                "backup_count": cls.LOG_BACKUP_COUNT,
                "enable_console": cls.LOG_ENABLE_CONSOLE,
                "enable_file": cls.LOG_ENABLE_FILE,
            },
            "webdriver": {
                "selenium_timeout": cls.SELENIUM_TIMEOUT,
                "appium_timeout": cls.APPIUM_TIMEOUT,
                "chrome_driver_path": cls.CHROME_DRIVER_PATH,
                "chrome_driver_version": cls.CHROME_DRIVER_VERSION,
                "chrome_driver_download_url": cls.CHROME_DRIVER_DOWNLOAD_URL,
                "appium_server_url": cls.APPIUM_SERVER_URL,
                "webdriver_mode": cls.WEBDRIVER_MODE,
                "remote_webdriver_url": cls.REMOTE_WEBDRIVER_URL,
                "selenium_hub_host": cls.SELENIUM_HUB_HOST,
                "selenium_hub_publish_port": cls.SELENIUM_HUB_PUBLISH_PORT,
                "selenium_hub_subscribe_port": cls.SELENIUM_HUB_SUBSCRIBE_PORT,
                "selenium_node_count": cls.SELENIUM_NODE_COUNT,
                "selenium_node_max_sessions": cls.SELENIUM_NODE_MAX_SESSIONS,
                "selenium_node_session_timeout": cls.SELENIUM_NODE_SESSION_TIMEOUT,
            },
            "device_pool": {
                "max_devices": cls.MAX_DEVICES,
                "cleanup_interval": cls.CLEANUP_INTERVAL,
                "device_timeout": cls.DEVICE_TIMEOUT,
                "device_connection_retry": cls.DEVICE_CONNECTION_RETRY,
                "device_connection_retry_delay": cls.DEVICE_CONNECTION_RETRY_DELAY,
            },
            "operation": {
                "default_timeout": cls.DEFAULT_TIMEOUT,
                "default_wait": cls.DEFAULT_WAIT,
                "element_wait_timeout": cls.ELEMENT_WAIT_TIMEOUT,
                "page_load_timeout": cls.PAGE_LOAD_TIMEOUT,
                "script_timeout": cls.SCRIPT_TIMEOUT,
            },
            "thread_pool": {
                "max_workers": cls.THREAD_POOL_MAX_WORKERS,
                "min_workers": cls.THREAD_POOL_MIN_WORKERS,
            },
            "connection_pool": {
                "max_connections": cls.CONNECTION_POOL_MAX_CONNECTIONS,
                "max_idle_time": cls.CONNECTION_POOL_MAX_IDLE_TIME,
            },
            "paths": {
                "project_root": cls.PROJECT_ROOT,
                "config_dir": cls.CONFIG_DIR,
                "logs_dir": cls.LOGS_DIR,
                "data_dir": cls.DATA_DIR,
                "cache_dir": cls.CACHE_DIR,
            },
            "network": {"name": cls.NETWORK_NAME, "timeout": cls.NETWORK_TIMEOUT},
            "certificates": {
                "install_certificates": cls.SE_INSTALL_CERTIFICATES,
                "certificates_dir": cls.CERTIFICATES_DIR,
            },
            "cache": {
                "enabled": cls.CACHE_ENABLED,
                "ttl": cls.CACHE_TTL,
                "max_size": cls.CACHE_MAX_SIZE,
            },
            "monitoring": {
                "metrics_enabled": cls.METRICS_ENABLED,
                "metrics_interval": cls.METRICS_INTERVAL,
                "auto_scale_enabled": cls.AUTO_SCALE_ENABLED,
            },
            "security": {
                "cors_enabled": cls.CORS_ENABLED,
                "cors_origins": cls.CORS_ORIGINS,
                "api_key_enabled": cls.API_KEY_ENABLED,
                "api_key_header": cls.API_KEY_HEADER,
            },
        }

    @classmethod
    def validate_config(cls) -> bool:
        """验证配置项的有效性"""
        try:
            # 验证端口范围
            if not (1 <= cls.API_PORT <= 65535):
                print(f"错误: API端口必须在1-65535之间，当前值: {cls.API_PORT}")
                return False

            # 验证超时时间
            if cls.SELENIUM_TIMEOUT <= 0:
                print(
                    f"错误: Selenium超时时间必须大于0，当前值: {cls.SELENIUM_TIMEOUT}"
                )
                return False

            # 验证线程池配置
            if cls.THREAD_POOL_MAX_WORKERS < cls.THREAD_POOL_MIN_WORKERS:
                print(f"错误: 最大工作线程数不能小于最小工作线程数")
                return False

            # 验证WebDriver模式
            if cls.WEBDRIVER_MODE not in ["local", "remote"]:
                print(
                    f"错误: WebDriver模式必须是 'local' 或 'remote'，当前值: {cls.WEBDRIVER_MODE}"
                )
                return False

            print("配置验证通过")
            return True

        except Exception as e:
            print(f"配置验证失败: {e}")
            return False

    @classmethod
    def print_config(cls) -> None:
        """打印当前配置"""
        print("=" * 50)
        print("当前配置:")
        print("=" * 50)

        config = cls.get_config()
        for section, items in config.items():
            print(f"\n[{section.upper()}]")
            for key, value in items.items():
                print(f"  {key}: {value}")

        print("=" * 50)


# 全局配置实例
settings = Settings()

# 验证配置
settings.validate_config()
