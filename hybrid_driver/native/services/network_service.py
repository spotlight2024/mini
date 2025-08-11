"""网络检查服务"""

import socket
import ipaddress
import netifaces
from typing import List, Tuple
from ..exceptions.executor_exceptions import NetworkException
from ..config import Config


class NetworkService:
    """网络检查服务类"""

    @staticmethod
    def is_ip_in_same_subnet(target_ip: str) -> bool:
        """
        检查目标IP是否与本机某个网络接口在同一网段

        Args:
            target_ip: 目标IP地址

        Returns:
            bool: 如果在同一网段返回True，否则返回False

        Raises:
            NetworkException: 当IP地址无效或网络检查失败时
        """
        try:
            target_addr = ipaddress.ip_address(target_ip)
        except ipaddress.AddressValueError as e:
            raise NetworkException(f"Invalid IP address: {target_ip}") from e

        try:
            # 获取所有网络接口
            interfaces = netifaces.interfaces()

            for interface in interfaces:
                # 获取接口的地址信息
                addrs = netifaces.ifaddresses(interface)

                # 检查IPv4地址
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        if 'addr' in addr_info and 'netmask' in addr_info:
                            try:
                                # 创建网络对象
                                local_ip = addr_info['addr']
                                netmask = addr_info['netmask']

                                # 跳过回环地址
                                if local_ip.startswith('127.'):
                                    continue

                                # 创建网络对象
                                network = ipaddress.IPv4Network(f"{local_ip}/{netmask}", strict=False)

                                # 检查目标IP是否在这个网络中
                                if target_addr in network:
                                    print(f"[NETWORK_CHECK] Target IP {target_ip} is in same subnet as {local_ip}/{netmask}")
                                    return True
                            except (ipaddress.AddressValueError, ValueError) as e:
                                print(f"[NETWORK_CHECK] Error processing interface {interface}: {e}")
                                continue

            print(f"[NETWORK_CHECK] Target IP {target_ip} is not in any local subnet")
            return False

        except Exception as e:
            raise NetworkException(f"Error checking network: {e}") from e

    @staticmethod
    def get_local_networks() -> List[Tuple[str, str]]:
        """
        获取本机所有网络接口的网络信息

        Returns:
            List[Tuple[str, str]]: 网络地址和子网掩码的列表
        """
        networks = []
        try:
            interfaces = netifaces.interfaces()

            for interface in interfaces:
                addrs = netifaces.ifaddresses(interface)

                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        if 'addr' in addr_info and 'netmask' in addr_info:
                            local_ip = addr_info['addr']
                            netmask = addr_info['netmask']

                            # 跳过回环地址
                            if not local_ip.startswith('127.'):
                                networks.append((local_ip, netmask))

            return networks
        except Exception as e:
            raise NetworkException(f"Error getting local networks: {e}") from e

    @staticmethod
    def validate_ip_port(ip: str, port: int) -> bool:
        """
        验证IP地址和端口的有效性

        Args:
            ip: IP地址
            port: 端口号

        Returns:
            bool: 验证通过返回True

        Raises:
            NetworkException: 当IP或端口无效时
        """
        try:
            ipaddress.ip_address(ip)
        except ipaddress.AddressValueError as e:
            raise NetworkException(f"Invalid IP address: {ip}") from e

        if not (1 <= port <= 65535):
            raise NetworkException(f"Invalid port number: {port}. Port must be between 1 and 65535")

        return True

    @staticmethod
    def resolve_target_ip(requested_ip: str) -> str:
        """
        解析目标IP地址，如果不在同一网段则返回127.0.0.1

        Args:
            requested_ip: 请求的IP地址

        Returns:
            str: 解析后的IP地址
        """
        try:
            if NetworkService.is_ip_in_same_subnet(requested_ip):
                print(f"[IP_CHECK] IP {requested_ip} is in same subnet, using original IP")
                return requested_ip
            else:
                print(f"[IP_CHECK] IP {requested_ip} is not in same subnet, using 127.0.0.1 instead")
                return "127.0.0.1"
        except NetworkException as e:
            print(f"[IP_CHECK] Error resolving IP {requested_ip}: {e}, using 127.0.0.1")
            return "127.0.0.1"