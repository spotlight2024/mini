from typing import Dict

class DeviceManager:
    def __init__(self):
        self.devices: Dict[str, dict] = {}

    def add_device(self, serial_id: str, ip: str, port: int):
        self.devices[serial_id] = {"ip": ip, "port": port}

    def get_device(self, serial_id: str):
        return self.devices.get(serial_id)

    def remove_device(self, serial_id: str):
        if serial_id in self.devices:
            del self.devices[serial_id] 