from typing import Dict

import adbutils
import logging
from adbutils import adb

from log_config import setup_logging

setup_logging()

class AndroidDevice:
    def __init__(self, serial_id: str):
        self.serial_id = serial_id

    @property
    def device(self):
        return adb.device(self.serial_id)

    
def track_devices():
    for event in adb.track_devices():
        logging.info(f"event : {event.present} {event.serial} {event.status}")

class DeviceManager:

    def connect(self, serial_id: str):
        logging.info(f"connect device {serial_id}")
        return None

    def disconnect(self, serial_id: str):
        logging.info(f"disconnect device {serial_id}")


if __name__ == "__main__":

    for device in adb.list():
        logging.info(f"device : {device}")
