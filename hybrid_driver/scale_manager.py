import subprocess
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)


@dataclass
class NodeInfo:
    """节点信息"""
    name: str
    status: str
    sessions: int
    max_sessions: int
    cpu_usage: float
    memory_usage: float
    uptime: str


class DockerScaleManager:
    """Docker容器扩缩容管理器"""
    
    def __init__(self, 
                 node_image: str = "selenium/node-chrome:4.33.0-20250606",
                 hub_host: str = "selenium-hub",
                 network_name: str = "spotlight-network"):
        self.node_image = node_image
        self.hub_host = hub_host
        self.network_name = network_name
        self.node_prefix = "selenium-node-chrome"
        
        logger.info(f"DockerScaleManager 初始化完成: {node_image}")
    
    def get_current_nodes(self) -> List[NodeInfo]:
        """获取当前运行的节点列表"""
        try:
            # 获取所有selenium节点容器
            cmd = [
                "docker", "ps", 
                "--filter", f"name={self.node_prefix}",
                "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                logger.error(f"获取节点列表失败: {result.stderr}")
                return []
            
            nodes = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                    
                parts = line.split('\t')
                if len(parts) >= 3:
                    name = parts[0]
                    status = parts[1]
                    
                    # 获取节点详细信息
                    node_info = self._get_node_details(name)
                    if node_info:
                        nodes.append(node_info)
            
            return nodes
            
        except Exception as e:
            logger.error(f"获取当前节点失败: {e}")
            return []
    
    def _get_node_details(self, node_name: str) -> Optional[NodeInfo]:
        """获取节点详细信息"""
        try:
            # 获取容器统计信息
            cmd = ["docker", "stats", node_name, "--no-stream", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                stats = json.loads(result.stdout.strip())
                
                # 解析CPU和内存使用率
                cpu_usage = self._parse_cpu_usage(stats.get('CPUPerc', '0%'))
                memory_usage = self._parse_memory_usage(stats.get('MemPerc', '0%'))
                
                return NodeInfo(
                    name=node_name,
                    status=stats.get('Status', 'unknown'),
                    sessions=0,  # 需要从Grid API获取
                    max_sessions=4,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    uptime=stats.get('RunningFor', 'unknown')
                )
                
        except Exception as e:
            logger.error(f"获取节点 {node_name} 详情失败: {e}")
        
        return None
    
    def _parse_cpu_usage(self, cpu_str: str) -> float:
        """解析CPU使用率字符串"""
        try:
            return float(cpu_str.replace('%', ''))
        except:
            return 0.0
    
    def _parse_memory_usage(self, mem_str: str) -> float:
        """解析内存使用率字符串"""
        try:
            return float(mem_str.replace('%', ''))
        except:
            return 0.0
    
    def scale_up(self, count: int = 1) -> bool:
        """扩容节点"""
        try:
            current_nodes = self.get_current_nodes()
            current_count = len(current_nodes)
            
            logger.info(f"开始扩容: 当前 {current_count} 个节点，增加 {count} 个")
            
            success_count = 0
            for i in range(count):
                node_name = f"{self.node_prefix}-{current_count + i + 1}"
                
                if self._create_node(node_name):
                    success_count += 1
                    logger.info(f"节点 {node_name} 创建成功")
                else:
                    logger.error(f"节点 {node_name} 创建失败")
            
            logger.info(f"扩容完成: 成功创建 {success_count}/{count} 个节点")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"扩容操作失败: {e}")
            return False
    
    def scale_down(self, count: int = 1) -> bool:
        """缩容节点"""
        try:
            current_nodes = self.get_current_nodes()
            current_count = len(current_nodes)
            
            if current_count <= 1:
                logger.warning("当前只有1个节点，无法继续缩容")
                return False
            
            logger.info(f"开始缩容: 当前 {current_count} 个节点，减少 {count} 个")
            
            # 选择要删除的节点（优先删除空闲节点）
            nodes_to_remove = self._select_nodes_to_remove(current_nodes, count)
            
            success_count = 0
            for node in nodes_to_remove:
                if self._remove_node(node.name):
                    success_count += 1
                    logger.info(f"节点 {node.name} 删除成功")
                else:
                    logger.error(f"节点 {node.name} 删除失败")
            
            logger.info(f"缩容完成: 成功删除 {success_count}/{count} 个节点")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"缩容操作失败: {e}")
            return False
    
    def _create_node(self, node_name: str) -> bool:
        """创建单个节点"""
        try:
            cmd = [
                "docker", "run", "-d",
                "--name", node_name,
                "--network", self.network_name,
                "-e", f"SE_EVENT_BUS_HOST={self.hub_host}",
                "-e", "SE_EVENT_BUS_PUBLISH_PORT=4442",
                "-e", "SE_EVENT_BUS_SUBSCRIBE_PORT=4443",
                "-e", "SE_NODE_MAX_SESSIONS=4",
                "-e", "SE_NODE_OVERRIDE_MAX_SESSIONS=true",
                "-e", "SE_NODE_SESSION_TIMEOUT=300",
                "-e", "SE_NODE_REGISTER_CYCLE=10000",
                "-e", "SE_NODE_REGISTER_PERIOD=10000",
                "-e", f"SE_NODE_HOST={node_name}",
                "-e", "SE_NODE_PORT=5555",
                "-v", "/dev/shm:/dev/shm",
                "--restart", "unless-stopped",
                "--memory", "2g",
                "--cpus", "1.0",
                self.node_image
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # 等待节点启动
                time.sleep(10)
                return True
            else:
                logger.error(f"创建节点失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"创建节点 {node_name} 异常: {e}")
            return False
    
    def _remove_node(self, node_name: str) -> bool:
        """删除单个节点"""
        try:
            # 先停止容器
            stop_cmd = ["docker", "stop", node_name]
            subprocess.run(stop_cmd, capture_output=True, text=True, timeout=30)
            
            # 再删除容器
            rm_cmd = ["docker", "rm", node_name]
            result = subprocess.run(rm_cmd, capture_output=True, text=True, timeout=30)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"删除节点 {node_name} 异常: {e}")
            return False
    
    def _select_nodes_to_remove(self, nodes: List[NodeInfo], count: int) -> List[NodeInfo]:
        """选择要删除的节点（优先删除空闲节点）"""
        # 按会话数排序，优先删除空闲节点
        sorted_nodes = sorted(nodes, key=lambda x: x.sessions)
        return sorted_nodes[:count]
    
    def get_scale_status(self) -> Dict:
        """获取扩缩容状态"""
        try:
            nodes = self.get_current_nodes()
            
            total_sessions = sum(node.sessions for node in nodes)
            avg_cpu = sum(node.cpu_usage for node in nodes) / len(nodes) if nodes else 0
            avg_memory = sum(node.memory_usage for node in nodes) / len(nodes) if nodes else 0
            
            return {
                'current_nodes': len(nodes),
                'total_sessions': total_sessions,
                'avg_cpu_usage': avg_cpu,
                'avg_memory_usage': avg_memory,
                'nodes': [
                    {
                        'name': node.name,
                        'status': node.status,
                        'sessions': node.sessions,
                        'cpu_usage': node.cpu_usage,
                        'memory_usage': node.memory_usage
                    }
                    for node in nodes
                ]
            }
            
        except Exception as e:
            logger.error(f"获取扩缩容状态失败: {e}")
            return {
                'current_nodes': 0,
                'total_sessions': 0,
                'avg_cpu_usage': 0,
                'avg_memory_usage': 0,
                'nodes': []
            }
    
    def cleanup_failed_nodes(self) -> int:
        """清理失败的节点"""
        try:
            cmd = [
                "docker", "ps", "-a",
                "--filter", f"name={self.node_prefix}",
                "--filter", "status=exited",
                "--format", "{{.Names}}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return 0
            
            failed_nodes = result.stdout.strip().split('\n')
            cleaned_count = 0
            
            for node_name in failed_nodes:
                if node_name.strip():
                    if self._remove_node(node_name.strip()):
                        cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个失败的节点")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理失败节点异常: {e}")
            return 0 