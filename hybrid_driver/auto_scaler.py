import time
import threading
import logging
import requests
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)


@dataclass
class ScalingMetrics:
    """扩容指标数据类"""
    timestamp: datetime
    active_sessions: int
    total_nodes: int
    queue_length: int
    cpu_usage: float
    memory_usage: float
    response_time: float


@dataclass
class ScalingConfig:
    """扩容配置类"""
    min_nodes: int = 2
    max_nodes: int = 20
    target_cpu_usage: float = 70.0
    target_memory_usage: float = 80.0
    target_response_time: float = 2.0
    scale_up_threshold: int = 5
    scale_down_threshold: int = 2
    cooldown_period: int = 300  # 5分钟冷却期
    check_interval: int = 30    # 30秒检查间隔


class SpotLightAutoScaler:
    """SpotLight 自动扩缩容管理器"""
    
    def __init__(self, config: Optional[ScalingConfig] = None):
        self.config = config or ScalingConfig()
        self.monitoring_thread = None
        self.is_monitoring = False
        self.last_scale_time = None
        self.metrics_history: List[ScalingMetrics] = []
        self.hub_url = "http://localhost:4444"
        self.api_url = "http://localhost:8002"
        
        # 扩容历史记录
        self.scale_history: List[Dict] = []
        
        logger.info(f"SpotLightAutoScaler 初始化完成，配置: {self.config}")
    
    def start_monitoring(self):
        """启动监控线程"""
        if self.is_monitoring:
            logger.warning("监控线程已在运行")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="AutoScaler-Monitor"
        )
        self.monitoring_thread.start()
        logger.info("自动扩容监控已启动")
    
    def stop_monitoring(self):
        """停止监控线程"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("自动扩容监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                self._check_and_scale()
                time.sleep(self.config.check_interval)
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(self.config.check_interval)
    
    def _check_and_scale(self):
        """检查并执行扩容"""
        try:
            # 获取当前指标
            metrics = self._collect_metrics()
            if not metrics:
                return
            
            self.metrics_history.append(metrics)
            
            # 保持历史记录在合理范围内
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-50:]
            
            # 检查是否需要扩容
            scale_action = self._evaluate_scaling(metrics)
            
            if scale_action:
                self._execute_scaling(scale_action, metrics)
                
        except Exception as e:
            logger.error(f"检查扩容时发生异常: {e}")
    
    def _collect_metrics(self) -> Optional[ScalingMetrics]:
        """收集系统指标"""
        try:
            # 获取Grid状态
            grid_status = self._get_grid_status()
            if not grid_status:
                return None
            
            # 获取API指标
            api_metrics = self._get_api_metrics()
            
            # 计算系统指标
            active_sessions = grid_status.get('active_sessions', 0)
            total_nodes = grid_status.get('total_nodes', 0)
            queue_length = grid_status.get('queue_length', 0)
            
            # 计算平均CPU和内存使用率
            cpu_usage = grid_status.get('avg_cpu_usage', 0.0)
            memory_usage = grid_status.get('avg_memory_usage', 0.0)
            response_time = api_metrics.get('avg_response_time', 0.0)
            
            return ScalingMetrics(
                timestamp=datetime.now(),
                active_sessions=active_sessions,
                total_nodes=total_nodes,
                queue_length=queue_length,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"收集指标时发生异常: {e}")
            return None
    
    def _get_grid_status(self) -> Optional[Dict]:
        """获取Selenium Grid状态"""
        try:
            response = requests.get(f"{self.hub_url}/wd/hub/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                nodes = data.get('value', {}).get('nodes', [])
                
                total_nodes = len(nodes)
                active_sessions = sum(node.get('sessions', []) for node in nodes)
                
                # 计算平均资源使用率
                cpu_usage = 0.0
                memory_usage = 0.0
                if nodes:
                    cpu_usage = sum(node.get('cpu_usage', 0.0) for node in nodes) / total_nodes
                    memory_usage = sum(node.get('memory_usage', 0.0) for node in nodes) / total_nodes
                
                return {
                    'total_nodes': total_nodes,
                    'active_sessions': active_sessions,
                    'queue_length': data.get('value', {}).get('queue_length', 0),
                    'avg_cpu_usage': cpu_usage,
                    'avg_memory_usage': memory_usage
                }
        except Exception as e:
            logger.error(f"获取Grid状态失败: {e}")
        
        return None
    
    def _get_api_metrics(self) -> Dict:
        """获取API指标"""
        try:
            response = requests.get(f"{self.api_url}/metrics", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"获取API指标失败: {e}")
        
        return {
            'avg_response_time': 0.0,
            'request_count': 0,
            'error_rate': 0.0
        }
    
    def _evaluate_scaling(self, metrics: ScalingMetrics) -> Optional[str]:
        """评估是否需要扩容"""
        # 检查冷却期
        if self.last_scale_time:
            time_since_last_scale = (datetime.now() - self.last_scale_time).total_seconds()
            if time_since_last_scale < self.config.cooldown_period:
                return None
        
        # 扩容条件检查
        should_scale_up = (
            metrics.active_sessions >= self.config.scale_up_threshold or
            metrics.cpu_usage > self.config.target_cpu_usage or
            metrics.memory_usage > self.config.target_memory_usage or
            metrics.response_time > self.config.target_response_time or
            metrics.queue_length > 0
        )
        
        # 缩容条件检查
        should_scale_down = (
            metrics.total_nodes > self.config.min_nodes and
            metrics.active_sessions <= self.config.scale_down_threshold and
            metrics.cpu_usage < self.config.target_cpu_usage * 0.5 and
            metrics.memory_usage < self.config.target_memory_usage * 0.5 and
            metrics.queue_length == 0
        )
        
        if should_scale_up and metrics.total_nodes < self.config.max_nodes:
            return "scale_up"
        elif should_scale_down:
            return "scale_down"
        
        return None
    
    def _execute_scaling(self, action: str, metrics: ScalingMetrics):
        """执行扩容操作"""
        try:
            if action == "scale_up":
                self._scale_up(metrics)
            elif action == "scale_down":
                self._scale_down(metrics)
            
            self.last_scale_time = datetime.now()
            
            # 记录扩容历史
            self.scale_history.append({
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'metrics': {
                    'active_sessions': metrics.active_sessions,
                    'total_nodes': metrics.total_nodes,
                    'cpu_usage': metrics.cpu_usage,
                    'memory_usage': metrics.memory_usage
                }
            })
            
            # 保持历史记录在合理范围内
            if len(self.scale_history) > 50:
                self.scale_history = self.scale_history[-25:]
                
        except Exception as e:
            logger.error(f"执行扩容操作失败: {e}")
    
    def _scale_up(self, metrics: ScalingMetrics):
        """扩容操作"""
        try:
            # 计算需要增加的节点数
            current_nodes = metrics.total_nodes
            target_nodes = min(current_nodes + 2, self.config.max_nodes)
            
            logger.info(f"开始扩容: {current_nodes} -> {target_nodes} 节点")
            
            # 调用扩容API
            scale_request = {
                'action': 'scale_up',
                'current_nodes': current_nodes,
                'target_nodes': target_nodes,
                'reason': f"CPU: {metrics.cpu_usage:.1f}%, Memory: {metrics.memory_usage:.1f}%, Sessions: {metrics.active_sessions}"
            }
            
            response = requests.post(
                f"{self.api_url}/scale/nodes",
                json=scale_request,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"扩容成功: {current_nodes} -> {target_nodes} 节点")
            else:
                logger.error(f"扩容失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"扩容操作异常: {e}")
    
    def _scale_down(self, metrics: ScalingMetrics):
        """缩容操作"""
        try:
            current_nodes = metrics.total_nodes
            target_nodes = max(current_nodes - 1, self.config.min_nodes)
            
            logger.info(f"开始缩容: {current_nodes} -> {target_nodes} 节点")
            
            # 调用缩容API
            scale_request = {
                'action': 'scale_down',
                'current_nodes': current_nodes,
                'target_nodes': target_nodes,
                'reason': f"CPU: {metrics.cpu_usage:.1f}%, Memory: {metrics.memory_usage:.1f}%, Sessions: {metrics.active_sessions}"
            }
            
            response = requests.post(
                f"{self.api_url}/scale/nodes",
                json=scale_request,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"缩容成功: {current_nodes} -> {target_nodes} 节点")
            else:
                logger.error(f"缩容失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"缩容操作异常: {e}")
    
    def get_status(self) -> Dict:
        """获取扩容状态"""
        return {
            'is_monitoring': self.is_monitoring,
            'config': {
                'min_nodes': self.config.min_nodes,
                'max_nodes': self.config.max_nodes,
                'target_cpu_usage': self.config.target_cpu_usage,
                'target_memory_usage': self.config.target_memory_usage,
                'check_interval': self.config.check_interval
            },
            'last_scale_time': self.last_scale_time.isoformat() if self.last_scale_time else None,
            'metrics_count': len(self.metrics_history),
            'scale_history_count': len(self.scale_history),
            'recent_metrics': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'active_sessions': m.active_sessions,
                    'total_nodes': m.total_nodes,
                    'cpu_usage': m.cpu_usage,
                    'memory_usage': m.memory_usage
                }
                for m in self.metrics_history[-5:]
            ],
            'recent_scales': self.scale_history[-5:]
        }
    
    def update_config(self, new_config: ScalingConfig):
        """更新扩容配置"""
        self.config = new_config
        logger.info(f"扩容配置已更新: {self.config}")
    
    def manual_scale(self, action: str, target_nodes: int) -> bool:
        """手动扩容"""
        try:
            if action not in ['scale_up', 'scale_down']:
                logger.error(f"无效的扩容操作: {action}")
                return False
            
            current_metrics = self._collect_metrics()
            if not current_metrics:
                logger.error("无法获取当前指标")
                return False
            
            if action == 'scale_up':
                self._scale_up(current_metrics)
            else:
                self._scale_down(current_metrics)
            
            return True
            
        except Exception as e:
            logger.error(f"手动扩容失败: {e}")
            return False 