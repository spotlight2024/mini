from typing import Dict

import adbutils
import logging
from adbutils import adb


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
    def __init__(self):
        self.devices: Dict[str, dict] = {}

    def connect(self, serial_id: str):
        logging.info(f"connect device {serial_id}")
        if serial_id in self.devices:
            logging.info(f"11111")
            androidDevice = self.devices[serial_id]
            # 检查设备是否在线
            device = androidDevice.device()
            if device:
                # 尝试重新连接设备
                androidDevice.device().connect(f"{androidDevice.devices[serial_id]['ip']}:{androidDevice.devices[serial_id]['port']}")
        else:
            logging.info(f"2222")
            androidDevice = AndroidDevice(serial_id)
            # androidDevice.device.
            self.devices[serial_id] = androidDevice


    def add_device(self, serial_id: str):
        self.devices[serial_id] = serial_id

    def get_device(self, serial_id: str):
        return self.devices.get(serial_id)

    def remove_device(self, serial_id: str):
        if serial_id in self.devices:
            del self.devices[serial_id]

            
    def connect_device(self, serial_id: str):
        for device in adb.device_list():
            if device.serial == serial_id:
                return device
        return None
    
    def disconnect_device(self, serial_id: str):
        adb = adbutils.AdbClient(host="127.0.0.1", port=5037)
        device = adb.device(serial_id)
        device.disconnect()

    def get_device_list(self):
        return adb.device_list()

if __name__ == "__main__":

    for device in adb.list():
        logging.info(f"device : {device}")

    # for event in adb.track_devices():
    #     logger.info(f"event : {event.present} {event.serial} {event.status}")