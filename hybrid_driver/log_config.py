import sys
from pathlib import Path
from loguru import logger

_DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "{extra[trace_id]: <36} | "
    "<cyan>{extra[logger_name]}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

_PERF_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "{extra[trace_id]: <36} | "
    "<cyan>{extra[logger_name]}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level> | "
    "<yellow>elapsed={extra[elapsed_ms]}ms</yellow>"
)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    rotation: str = "200 MB",
    retention: str = "14 days",
    compression: str = "zip",
    intercept_third_party: bool = True,
) -> None:
    """
    配置 loguru 日志系统，统一控制输出格式、文件分发与上下文字段。

    Args:
        log_level: 全局日志级别
        log_dir: 日志文件目录
        rotation: 文件轮转策略
        retention: 文件保留时间
        compression: 日志压缩格式
        intercept_third_party: 是否单独收集第三方库日志
    """

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.configure(
        extra={
            "trace_id": "-",
            "device_id": "-",
            "operation": "-",
            "logger_name": "root",
            "elapsed_ms": None,
        }
    )

    # 控制台输出
    logger.add(
        sys.stdout,
        level=log_level,
        format=_DEFAULT_FORMAT,
        colorize=True,
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    # 主业务日志
    logger.add(
        str(log_path / "spot_light_{time:YYYYMMDD}.log"),
        level=log_level,
        format=_DEFAULT_FORMAT,
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    # 错误日志
    logger.add(
        str(log_path / "spot_light_errors.log"),
        level="ERROR",
        format=_DEFAULT_FORMAT,
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    # 性能日志（依赖 extra["elapsed_ms"] 标记）
    logger.add(
        str(log_path / "spot_light_performance_{time:YYYYMMDD}.log"),
        level="INFO",
        format=_PERF_FORMAT,
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("elapsed_ms") is not None,
        backtrace=False,
        diagnose=False,
    )

    if intercept_third_party:
        logger.add(
            str(log_path / "spot_light_third_party_{time:YYYYMMDD}.log"),
            level="WARNING",
            format=_DEFAULT_FORMAT,
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            enqueue=True,
            filter=lambda record: any(
                keyword in (record["name"] or "").lower()
                for keyword in ("selenium", "urllib3", "requests")
            ),
            backtrace=False,
            diagnose=False,
        )


def get_logger(name: str | None = None, **extra: object):
    """
    获取绑定上下文的日志记录器。

    Args:
        name: 模块或业务名称
        extra: 额外的上下文字段（会覆盖默认值）
    """

    bound = logger
    payload = extra.copy()
    if name is not None:
        payload.setdefault("logger_name", name)
    if payload:
        bound = bound.bind(**payload)
    return bound