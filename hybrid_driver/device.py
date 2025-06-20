from typing import Dict

import adbutils
import logging
from adbutils import adb

from log_config import setup_logging

setup_logging()

class DeviceManager:

    def connect(self, serial_id: str):
        logging.info(f"connect device {serial_id}")

        target_device = None
        for d in adbutils.adb.device_list():
            if d.serial == serial_id:
                target_device = adb.device(d.serial)
                break

        print(target_device.info["state"])

        if target_device is None:
            logging.info(f"connect device {serial_id} failed")



        return None

    def disconnect(self, serial_id: str):
        logging.info(f"disconnect device {serial_id}")


if __name__ == "__main__":

    for device in adb.list():
        logging.info(f"device : {device}")
