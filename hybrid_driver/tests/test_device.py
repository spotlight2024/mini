import pytest
from unittest.mock import patch, MagicMock
from device import DeviceManager
import adbutils
import logging

# 测试设备存在时 connect_device 返回 device 对象
def test_connect_device_found():
    manager = DeviceManager()
    result = manager.connect_device("test_serial")

# 测试设备不存在时 connect_device 返回 None
def test_connect_device_not_found():
    manager = DeviceManager()
    fake_device = MagicMock()
    fake_device.serial = "other_serial"
    with patch("adbutils.adb.device_list", return_value=[fake_device]), \
         patch("adbutils.adb.forward_list", return_value=[]):
        result = manager.connect_device("test_serial")
        assert result is None 


def test_connect_device_real():
    devices = adbutils.adb.device_list()
    for device in devices:
        logging.info(device.serial)

    for event in adbutils.adb.track_devices():
        logging.info("%s %s %s", event.present, event.serial, event.status)
