"""
执行器工厂类
统一管理不同类型的自动化执行器
"""

from typing import Type, Optional, Dict, Any
from hybrid_driver.webdriver.web_executor import WebExecutor
from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor
from hybrid_driver.webdriver.appium_executor import AppiumExecutor
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)


class ExecutorFactory:
    """执行器工厂类"""
    
    _executors: Dict[str, Type[WebExecutor]] = {
        "selenium": SeleniumWebExecutor,
        "appium": AppiumExecutor,
    }
    
    @classmethod
    def register_executor(cls, name: str, executor_cls: Type[WebExecutor]) -> None:
        """注册新的执行器类型"""
        cls._executors[name] = executor_cls
        logger.info(f"注册执行器: {name} -> {executor_cls.__name__}")
    
    @classmethod
    def get_executor(cls, executor_type: str = "selenium", **kwargs) -> WebExecutor:
        """获取执行器实例"""
        if executor_type not in cls._executors:
            raise ValueError(f"未知的执行器类型: {executor_type}")
        
        executor_cls = cls._executors[executor_type]
        
        # 根据执行器类型传入不同的参数
        if executor_type == "selenium":
            return executor_cls()
        elif executor_type == "appium":
            appium_server_url = kwargs.get("appium_server_url", "http://localhost:4723")
            capabilities = kwargs.get("capabilities", {})
            return executor_cls(appium_server_url=appium_server_url, capabilities=capabilities)
        else:
            # 对于其他执行器，直接传入所有参数
            return executor_cls(**kwargs)
    
    @classmethod
    def get_available_executors(cls) -> list[str]:
        """获取所有可用的执行器类型"""
        return list(cls._executors.keys())


# 默认工厂实例
executor_factory = ExecutorFactory() 