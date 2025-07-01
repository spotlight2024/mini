import time
import threading
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)


@dataclass
class RequestMetrics:
    """请求指标数据类"""
    timestamp: datetime
    endpoint: str
    method: str
    response_time: float
    status_code: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int


class SpotLightMetrics:
    """SpotLight 指标收集器"""
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        
        # 请求指标历史
        self.request_history: deque = deque(maxlen=max_history_size)
        
        # 系统指标历史
        self.system_history: deque = deque(maxlen=max_history_size)
        
        # 实时统计
        self.request_stats = defaultdict(int)
        self.error_stats = defaultdict(int)
        self.response_time_stats = defaultdict(list)
        
        # 监控线程
        self.monitoring_thread = None
        self.is_monitoring = False
        
        logger.info("SpotLightMetrics 初始化完成")
    
    def start_monitoring(self):
        """启动系统指标监控"""
        if self.is_monitoring:
            logger.warning("指标监控已在运行")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._system_monitoring_loop,
            daemon=True,
            name="Metrics-Monitor"
        )
        self.monitoring_thread.start()
        logger.info("系统指标监控已启动")
    
    def stop_monitoring(self):
        """停止系统指标监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("系统指标监控已停止")
    
    def record_request(self, endpoint: str, method: str, response_time: float, 
                      status_code: int, error_message: Optional[str] = None):
        """记录请求指标"""
        try:
            metrics = RequestMetrics(
                timestamp=datetime.now(),
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=status_code,
                success=status_code < 400,
                error_message=error_message
            )
            
            self.request_history.append(metrics)
            
            # 更新统计
            key = f"{method} {endpoint}"
            self.request_stats[key] += 1
            
            if not metrics.success:
                self.error_stats[key] += 1
            
            self.response_time_stats[key].append(response_time)
            
            # 保持响应时间统计在合理范围内
            if len(self.response_time_stats[key]) > 100:
                self.response_time_stats[key] = self.response_time_stats[key][-50:]
                
        except Exception as e:
            logger.error(f"记录请求指标失败: {e}")
    
    def _system_monitoring_loop(self):
        """系统指标监控循环"""
        while self.is_monitoring:
            try:
                metrics = self._collect_system_metrics()
                if metrics:
                    self.system_history.append(metrics)
                time.sleep(30)  # 每30秒收集一次系统指标
            except Exception as e:
                logger.error(f"系统指标监控异常: {e}")
                time.sleep(30)
    
    def _collect_system_metrics(self) -> Optional[SystemMetrics]:
        """收集系统指标"""
        try:
            import psutil
            
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # 网络IO
            network_io = psutil.net_io_counters()
            network_stats = {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv
            }
            
            # 活跃连接数
            active_connections = len(psutil.net_connections())
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_stats,
                active_connections=active_connections
            )
            
        except ImportError:
            logger.warning("psutil 未安装，无法收集系统指标")
            return None
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return None
    
    def get_metrics(self) -> Dict:
        """获取所有指标"""
        try:
            # 计算请求统计
            total_requests = sum(self.request_stats.values())
            total_errors = sum(self.error_stats.values())
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            # 计算平均响应时间
            avg_response_time = 0.0
            if self.response_time_stats:
                all_response_times = []
                for times in self.response_time_stats.values():
                    all_response_times.extend(times)
                if all_response_times:
                    avg_response_time = sum(all_response_times) / len(all_response_times)
            
            # 获取最近的系统指标
            recent_system_metrics = None
            if self.system_history:
                recent_system_metrics = self.system_history[-1]
            
            # 计算各端点的统计
            endpoint_stats = {}
            for key, count in self.request_stats.items():
                error_count = self.error_stats.get(key, 0)
                response_times = self.response_time_stats.get(key, [])
                avg_rt = sum(response_times) / len(response_times) if response_times else 0
                
                endpoint_stats[key] = {
                    'total_requests': count,
                    'error_count': error_count,
                    'error_rate': (error_count / count * 100) if count > 0 else 0,
                    'avg_response_time': avg_rt,
                    'min_response_time': min(response_times) if response_times else 0,
                    'max_response_time': max(response_times) if response_times else 0
                }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_requests': total_requests,
                'total_errors': total_errors,
                'error_rate': error_rate,
                'avg_response_time': avg_response_time,
                'endpoint_stats': endpoint_stats,
                'system_metrics': {
                    'cpu_usage': recent_system_metrics.cpu_usage if recent_system_metrics else 0,
                    'memory_usage': recent_system_metrics.memory_usage if recent_system_metrics else 0,
                    'disk_usage': recent_system_metrics.disk_usage if recent_system_metrics else 0,
                    'active_connections': recent_system_metrics.active_connections if recent_system_metrics else 0
                } if recent_system_metrics else None,
                'history_sizes': {
                    'request_history': len(self.request_history),
                    'system_history': len(self.system_history)
                }
            }
            
        except Exception as e:
            logger.error(f"获取指标失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_recent_requests(self, limit: int = 50) -> List[Dict]:
        """获取最近的请求记录"""
        try:
            recent_requests = list(self.request_history)[-limit:]
            return [
                {
                    'timestamp': req.timestamp.isoformat(),
                    'endpoint': req.endpoint,
                    'method': req.method,
                    'response_time': req.response_time,
                    'status_code': req.status_code,
                    'success': req.success,
                    'error_message': req.error_message
                }
                for req in recent_requests
            ]
        except Exception as e:
            logger.error(f"获取最近请求记录失败: {e}")
            return []
    
    def get_system_history(self, hours: int = 24) -> List[Dict]:
        """获取系统指标历史"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [
                metrics for metrics in self.system_history
                if metrics.timestamp >= cutoff_time
            ]
            
            return [
                {
                    'timestamp': metrics.timestamp.isoformat(),
                    'cpu_usage': metrics.cpu_usage,
                    'memory_usage': metrics.memory_usage,
                    'disk_usage': metrics.disk_usage,
                    'active_connections': metrics.active_connections
                }
                for metrics in recent_metrics
            ]
        except Exception as e:
            logger.error(f"获取系统指标历史失败: {e}")
            return []
    
    def clear_history(self):
        """清空历史记录"""
        self.request_history.clear()
        self.system_history.clear()
        self.request_stats.clear()
        self.error_stats.clear()
        self.response_time_stats.clear()
        logger.info("指标历史记录已清空")
    
    def get_health_status(self) -> Dict:
        """获取健康状态"""
        try:
            # 检查最近的错误率
            recent_requests = list(self.request_history)[-100:]  # 最近100个请求
            if recent_requests:
                error_count = sum(1 for req in recent_requests if not req.success)
                error_rate = (error_count / len(recent_requests)) * 100
                
                # 检查平均响应时间
                avg_response_time = sum(req.response_time for req in recent_requests) / len(recent_requests)
                
                # 健康状态判断
                is_healthy = (
                    error_rate < 5.0 and  # 错误率小于5%
                    avg_response_time < 2.0  # 平均响应时间小于2秒
                )
                
                return {
                    'status': 'healthy' if is_healthy else 'unhealthy',
                    'error_rate': error_rate,
                    'avg_response_time': avg_response_time,
                    'recent_requests_count': len(recent_requests),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'unknown',
                    'message': 'No recent requests',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"获取健康状态失败: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            } 