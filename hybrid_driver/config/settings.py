"""
应用配置管理
统一管理所有配置项，包括API配置、WebDriver配置、设备池配置等
"""

import os
from typing import Optional


class Settings:
    """应用配置管理类"""
    
    # API服务配置
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8002"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/hybrid_driver.log")
    LOG_MAX_SIZE: str = os.getenv("LOG_MAX_SIZE", "10MB")
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # WebDriver配置
    SELENIUM_TIMEOUT: int = int(os.getenv("SELENIUM_TIMEOUT", "30"))
    APPIUM_TIMEOUT: int = int(os.getenv("APPIUM_TIMEOUT", "30"))
    CHROME_DRIVER_PATH: Optional[str] = os.getenv("CHROME_DRIVER_PATH")
    APPIUM_SERVER_URL: str = os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")
    WEBDRIVER_MODE: str = os.getenv("WEBDRIVER_MODE", "local")  # 可选值：'local' 或 'remote'
    REMOTE_WEBDRIVER_URL: Optional[str] = os.getenv("REMOTE_WEBDRIVER_URL")
    
    # 设备池配置
    MAX_DEVICES: int = int(os.getenv("MAX_DEVICES", "10"))
    CLEANUP_INTERVAL: int = int(os.getenv("CLEANUP_INTERVAL", "300"))
    DEVICE_TIMEOUT: int = int(os.getenv("DEVICE_TIMEOUT", "60"))
    
    # 操作配置
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "10"))
    DEFAULT_WAIT: int = int(os.getenv("DEFAULT_WAIT", "5"))
    
    # 文件路径配置
    PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CONFIG_DIR: str = os.path.join(PROJECT_ROOT, "config")
    LOGS_DIR: str = os.path.join(PROJECT_ROOT, "logs")
    
    @classmethod
    def get_config(cls) -> dict:
        """获取所有配置项"""
        return {
            "api": {
                "host": cls.API_HOST,
                "port": cls.API_PORT,
                "reload": cls.API_RELOAD
            },
            "logging": {
                "level": cls.LOG_LEVEL,
                "format": cls.LOG_FORMAT,
                "file": cls.LOG_FILE,
                "max_size": cls.LOG_MAX_SIZE,
                "backup_count": cls.LOG_BACKUP_COUNT
            },
            "webdriver": {
                "selenium_timeout": cls.SELENIUM_TIMEOUT,
                "appium_timeout": cls.APPIUM_TIMEOUT,
                "chrome_driver_path": cls.CHROME_DRIVER_PATH,
                "appium_server_url": cls.APPIUM_SERVER_URL
            },
            "device_pool": {
                "max_devices": cls.MAX_DEVICES,
                "cleanup_interval": cls.CLEANUP_INTERVAL,
                "device_timeout": cls.DEVICE_TIMEOUT
            },
            "operation": {
                "default_timeout": cls.DEFAULT_TIMEOUT,
                "default_wait": cls.DEFAULT_WAIT
            },
            "paths": {
                "project_root": cls.PROJECT_ROOT,
                "config_dir": cls.CONFIG_DIR,
                "logs_dir": cls.LOGS_DIR
            }
        }


# 全局配置实例
settings = Settings() 