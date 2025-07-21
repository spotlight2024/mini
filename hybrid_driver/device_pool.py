import threading
from typing import Optional
import adbutils
import logging
import time

from hybrid_driver.device.android_device import AndroidDevice
from hybrid_driver.webdriver.executor_factory import executor_factory
from hybrid_driver.api.models import ConnectConfig

from hybrid_driver.log_config import setup_logging
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)

setup_logging()


class DevicePool:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 确保初始化代码只执行一次
        if not hasattr(self, '_initialized'):
            self.pool = {}  # serial_id -> AndroidDevice
            self.lock = threading.Lock()
            self._start_cleanup_task()
            self._initialized = True

    def connect(self, config: ConnectConfig) -> AndroidDevice:
        """连接设备并返回设备实例"""
        with self.lock:
            logger.info(f"start connect device: ${config}")
            # 确保 config 是 ConnectConfig 实例
            if not isinstance(config, ConnectConfig):
                logger.error(f"config 不是 ConnectConfig 实例，而是 {type(config)}: {config}")
                raise ValueError(f"Expected ConnectConfig instance, got {type(config)}")
            
            try:
                config_dict = config.model_dump()
                logger.info(f"[DevicePool] 尝试连接 config={config_dict}")
            except AttributeError as e:
                logger.error(f"config 对象没有 model_dump 方法: {e}")
                config_dict = {"serial_id": config.serial_id if hasattr(config, 'serial_id') else str(config)}
                logger.info(f"[DevicePool] 尝试连接 config={config_dict}")
            
            device = self.pool.get(config.serial_id)

            # 如果设备不存在或已断开，创建新设备
            if device is None or not device.is_connected():
                try:
                    # 使用 ExecutorFactory 创建设备
                    device = AndroidDevice(
                        serial_id=config.serial_id, 
                        executor_type=config.executor_type
                    )
                    if device.connect(config):
                        self.pool[config.serial_id] = device
                        logger.info(f"[DevicePool] 设备连接成功 serial_id={config.serial_id}")
                    else:
                        logger.error(f"[DevicePool] 设备连接失败 serial_id={config.serial_id}")
                        raise RuntimeError(f"Failed to connect device: {config.serial_id}")
                except Exception as e:
                    logger.error(f"[DevicePool] 设备连接失败 serial_id={config.serial_id}: {e}")
                    raise
            else:
                logger.info(f"[DevicePool] 设备已存在且存活 serial_id={config.serial_id}")

            return device

    def connect_legacy(self, serial_id, ip=None, port=None) -> AndroidDevice:
        """向后兼容的连接方法"""
        config = ConnectConfig(
            serial_id=serial_id,
            user_id="legacy_user",  # 默认用户ID
            ip=ip,
            port=port
        )
        return self.connect(config)

    def get(self, serial_id) -> Optional[AndroidDevice]:
        """获取设备实例，如果不存在返回 None"""
        with self.lock:
            logger.info(f"[DevicePool] 获取设备 serial_id={serial_id}")
            return self.pool.get(serial_id)

    def disconnect(self, serial_id):
        """断开设备连接并释放资源"""
        with self.lock:
            logger.info(f"[DevicePool] 断开设备 serial_id={serial_id}")
            device = self.pool.pop(serial_id, None)
            if device:
                try:
                    device.disconnect()
                except Exception as e:
                    logger.error(f"[DevicePool] 断开设备失败 serial_id={serial_id}: {e}")

    def _start_cleanup_task(self, interval=600):
        """启动清理任务，定期清理空闲设备"""

        def task():
            while True:
                time.sleep(interval)
                try:
                    with self.lock:
                        for serial_id in list(self.pool.keys()):
                            device = self.pool[serial_id]
                            if not device.is_connected():
                                self.disconnect(serial_id)
                except Exception as e:
                    logger.error(f"[DevicePool] 清理任务异常: {e}")

        t = threading.Thread(target=task, daemon=True)
        t.start()

    def __enter__(self):
        """支持上下文管理器"""
        logger.info("[DevicePool] enter")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info("[DevicePool] exit")
        """退出上下文时清理所有设备"""
        # for serial_id in list(self.pool.keys()):
        #     self.disconnect(serial_id)


if __name__ == "__main__":
    config = ConnectConfig(
        serial_id="JJGICIN7QOAELNGI",
        user_id="test_user"
    )
    DevicePool().connect(config)
