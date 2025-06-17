from typing import Optional, Any, Dict
from loguru import logger

class Logger:
    """日志工具类，提供统一的日志接口"""
    
    def __init__(self, name: str):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称，通常使用 __name__
        """
        self.logger = logger.bind(name=name)
    
    def _format_context(self, **kwargs) -> Dict[str, Any]:
        """
        格式化上下文信息
        
        Args:
            **kwargs: 上下文信息
            
        Returns:
            格式化后的上下文信息
        """
        context = {}
        for key, value in kwargs.items():
            if isinstance(value, (str, int, float, bool)):
                context[key] = value
            else:
                context[key] = str(value)
        return context
    
    def debug(self, message: str, **kwargs):
        """记录调试级别的日志"""
        self.logger.debug(message, **self._format_context(**kwargs))
    
    def info(self, message: str, **kwargs):
        """记录信息级别的日志"""
        self.logger.info(message, **self._format_context(**kwargs))
    
    def warning(self, message: str, **kwargs):
        """记录警告级别的日志"""
        self.logger.warning(message, **self._format_context(**kwargs))
    
    def error(self, message: str, exc: Optional[Exception] = None, **kwargs):
        """
        记录错误级别的日志
        
        Args:
            message: 错误消息
            exc: 异常对象，如果提供则记录完整的堆栈信息
            **kwargs: 额外的上下文信息
        """
        if exc:
            self.logger.exception(message, **self._format_context(**kwargs))
        else:
            self.logger.error(message, **self._format_context(**kwargs))
    
    def exception(self, message: str, **kwargs):
        """记录异常级别的日志，自动包含堆栈信息"""
        self.logger.exception(message, **self._format_context(**kwargs)) 