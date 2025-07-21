import os
import sys
from datetime import datetime
from pathlib import Path
from loguru import logger

def setup_logging(
    log_level="TRACE",
    log_dir="logs",
    rotation="10 MB",
    retention="1 week",
    compression="zip",
    format_str="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    intercept_third_party=True
):
    """
    配置 loguru 日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件目录
        rotation: 日志文件轮转大小
        retention: 日志保留时间
        compression: 日志压缩格式
        format_str: 日志格式
        intercept_third_party: 是否拦截第三方库的日志
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 生成日志文件名，包含日期
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = log_path / f"spot_light_{current_date}.log"
    
    # 移除默认的处理器
    logger.remove()
    
    # 添加控制台处理器
    logger.add(
        sys.stderr,
        format=format_str,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 添加文件处理器
    logger.add(
        str(log_file),
        format=format_str,
        level=log_level,
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )
    
    # 添加错误日志文件处理器
    logger.add(
        str(log_path / "error_{time}.log"),
        format=format_str,
        level="ERROR",
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )
    
    # 添加 Selenium 日志文件处理器
    logger.add(
        str(log_path / "selenium_{time}.log"),
        filter=lambda record: "selenium" in record["name"].lower(),
        level="WARNING",
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )
    
    # 添加性能日志文件处理器
    logger.add(
        str(log_path / "performance_{time}.log"),
        filter=lambda record: "performance" in record["extra"],
        level="INFO",
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> | <yellow>耗时: {extra[elapsed]}ms</yellow>"
    )
    
    # 拦截第三方库的日志
    if intercept_third_party:
        # 设置第三方库的日志级别
        logger.add(
            str(log_path / "third_party_{time}.log"),
            filter=lambda record: any(lib in record["name"].lower() for lib in ["selenium", "urllib3", "requests"]),
            level="WARNING",
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8"
        )
    
    # 添加日志上下文
    logger.configure(
        extra={
            "trace_id": None,
            "device_id": None,
            "operation": None
        }
    )
    
    return logger

def get_logger(name=None):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
    """
    if name:
        return logger.bind(name=name)
    return logger 