#!/usr/bin/env python3
"""
性能配置和监控工具
用于优化淘宝搜索API的性能参数
"""
import os
import psutil
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from hybrid_driver.config.settings import Settings

@dataclass
class PerformanceConfig:
    """性能配置类"""
    
    # 线程池配置
    max_workers: int = 50
    min_workers: int = 10
    
    # 缓存配置
    proxy_cache_ttl: int = 300  # 5分钟
    proxy_cache_size: int = 100
    
    # 超时配置
    default_timeout: int = 120
    connection_timeout: int = 30
    search_timeout: int = 90
    
    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 内存配置
    max_memory_mb: int = 512
    memory_check_interval: int = 30
    
    # 并发配置
    max_concurrent_sessions: int = 10
    session_queue_size: int = 50
    
    @classmethod
    def from_settings(cls, settings: Settings) -> 'PerformanceConfig':
        """从Settings创建性能配置"""
        return cls(
            max_workers=getattr(settings, 'THREAD_POOL_MAX_WORKERS', 50),
            connection_timeout=getattr(settings, 'SELENIUM_TIMEOUT', 30),
            proxy_cache_ttl=getattr(settings, 'CACHE_TTL', 300),
        )
    
    def create_thread_pool(self) -> ThreadPoolExecutor:
        """创建线程池"""
        return ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="TaobaoSearch"
        )

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.metrics: Dict[str, Any] = {}
        self.start_time = time.time()
        
    def start_session(self, session_id: str):
        """开始会话监控"""
        self.metrics[session_id] = {
            'start_time': time.time(),
            'memory_start': psutil.virtual_memory().used,
            'cpu_start': psutil.cpu_percent(),
        }
    
    def end_session(self, session_id: str):
        """结束会话监控"""
        if session_id in self.metrics:
            session_data = self.metrics[session_id]
            session_data.update({
                'end_time': time.time(),
                'memory_end': psutil.virtual_memory().used,
                'cpu_end': psutil.cpu_percent(),
                'duration': time.time() - session_data['start_time'],
                'memory_delta': psutil.virtual_memory().used - session_data['memory_start']
            })
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_mb': psutil.virtual_memory().used / 1024 / 1024,
            'active_sessions': len(self.metrics),
            'uptime_seconds': time.time() - self.start_time
        }
    
    def check_memory_threshold(self) -> bool:
        """检查内存是否超过阈值"""
        current_memory_mb = psutil.virtual_memory().used / 1024 / 1024
        return current_memory_mb > self.config.max_memory_mb
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        completed_sessions = [
            s for s in self.metrics.values() 
            if 'end_time' in s
        ]
        
        if not completed_sessions:
            return {"message": "暂无完成的会话"}
        
        durations = [s['duration'] for s in completed_sessions]
        memory_deltas = [s['memory_delta'] for s in completed_sessions]
        
        return {
            'total_sessions': len(completed_sessions),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'avg_memory_delta_mb': sum(memory_deltas) / len(memory_deltas) / 1024 / 1024,
            'system_metrics': self.get_system_metrics()
        }

# 全局性能配置实例
performance_config = PerformanceConfig()
performance_monitor = PerformanceMonitor(performance_config)

