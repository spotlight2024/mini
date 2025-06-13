import threading
from typing import Optional
import adbutils
import logging
import time

from device.android_device import AndroidDevice
from webdriver.selenium_executor import SeleniumWebExecutor

from log_config import setup_logging

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

    def connect(self, serial_id, ip=None, port=None) -> AndroidDevice:
        """连接设备并返回设备实例"""
        with self.lock:
            logging.info(f"[DevicePool] 尝试连接 serial_id={serial_id}, ip={ip}, port={port}")
            device = self.pool.get(serial_id)

            # 如果设备不存在或已断开，创建新设备
            if device is None or not device.is_connected():
                try:
                    device = AndroidDevice(serial_id, web_execute_cls=SeleniumWebExecutor)
                    if device.connect(ip=ip, port=port):
                        self.pool[serial_id] = device
                        logging.info(f"[DevicePool] 设备连接成功 serial_id={serial_id}")
                    else:
                        logging.error(f"[DevicePool] 设备连接失败 serial_id={serial_id}")
                        raise RuntimeError(f"Failed to connect device: {serial_id}")
                except Exception as e:
                    logging.error(f"[DevicePool] 设备连接失败 serial_id={serial_id}: {e}")
                    raise
            else:
                logging.info(f"[DevicePool] 设备已存在且存活 serial_id={serial_id}")

            return device

    def get(self, serial_id) -> Optional[AndroidDevice]:
        """获取设备实例，如果不存在返回 None"""
        with self.lock:
            logging.info(f"[DevicePool] 获取设备 serial_id={serial_id}")
            return self.pool.get(serial_id)

    def disconnect(self, serial_id):
        """断开设备连接并释放资源"""
        with self.lock:
            logging.info(f"[DevicePool] 断开设备 serial_id={serial_id}")
            device = self.pool.pop(serial_id, None)
            if device:
                try:
                    device.disconnect()
                except Exception as e:
                    logging.error(f"[DevicePool] 断开设备失败 serial_id={serial_id}: {e}")

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
                    logging.error(f"[DevicePool] 清理任务异常: {e}")

        t = threading.Thread(target=task, daemon=True)
        t.start()

    def __enter__(self):
        """支持上下文管理器"""
        logging.info("[DevicePool] enter")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info("[DevicePool] exit")
        """退出上下文时清理所有设备"""
        # for serial_id in list(self.pool.keys()):
        #     self.disconnect(serial_id)


if __name__ == "__main__":
    DevicePool().connect("JJGICIN7QOAELNGI")
