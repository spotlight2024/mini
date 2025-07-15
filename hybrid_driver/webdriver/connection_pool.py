import asyncio
import time
from typing import Dict, Optional, List, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)

class ConnectionStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    CONNECTING = "connecting"

@dataclass
class ConnectionInfo:
    driver: Any
    status: ConnectionStatus
    last_used: float
    created_time: float
    serial_id: str
    error_count: int = 0

class WebDriverConnectionPool:
    """WebDriver 连接池 - 复用连接，减少网络开销"""
    
    def __init__(self, max_connections_per_device=3, max_idle_time=300):
        self.connections: Dict[str, List[ConnectionInfo]] = {}
        self.connection_locks: Dict[str, asyncio.Lock] = {}
        self.max_connections_per_device = max_connections_per_device
        self.max_idle_time = max_idle_time
        self.thread_pool = ThreadPoolExecutor(max_workers=50)
        
        # 启动清理任务
        asyncio.create_task(self._cleanup_idle_connections())
    
    async def get_connection(self, serial_id: str, create_func) -> Optional[Any]:
        """获取可用的连接"""
        lock = self.connection_locks.setdefault(serial_id, asyncio.Lock())
        
        async with lock:
            connections = self.connections.get(serial_id, [])
            
            # 1. 查找空闲连接
            for conn_info in connections:
                if conn_info.status == ConnectionStatus.IDLE:
                    # 检查连接是否还有效
                    if await self._is_connection_alive(conn_info.driver):
                        conn_info.status = ConnectionStatus.BUSY
                        conn_info.last_used = time.time()
                        logger.info(f"复用连接: {serial_id}")
                        return conn_info.driver
                    else:
                        # 连接已失效，标记为错误
                        conn_info.status = ConnectionStatus.ERROR
            
            # 2. 清理错误连接
            connections = [c for c in connections if c.status != ConnectionStatus.ERROR]
            
            # 3. 创建新连接（如果未达到最大连接数）
            if len(connections) < self.max_connections_per_device:
                try:
                    logger.info(f"创建新连接: {serial_id}")
                    driver = await self._create_connection_async(create_func)
                    conn_info = ConnectionInfo(
                        driver=driver,
                        status=ConnectionStatus.BUSY,
                        last_used=time.time(),
                        created_time=time.time(),
                        serial_id=serial_id
                    )
                    connections.append(conn_info)
                    self.connections[serial_id] = connections
                    return driver
                except Exception as e:
                    logger.error(f"创建连接失败: {serial_id}, {e}")
                    return None
            
            # 4. 等待可用连接
            logger.info(f"等待可用连接: {serial_id}")
            return await self._wait_for_available_connection(serial_id)
    
    async def release_connection(self, serial_id: str, driver: Any):
        """释放连接回池"""
        lock = self.connection_locks.get(serial_id)
        if not lock:
            return
        
        async with lock:
            connections = self.connections.get(serial_id, [])
            for conn_info in connections:
                if conn_info.driver == driver:
                    conn_info.status = ConnectionStatus.IDLE
                    conn_info.last_used = time.time()
                    logger.debug(f"释放连接: {serial_id}")
                    break
    
    async def _create_connection_async(self, create_func) -> Any:
        """异步创建连接"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, create_func)
    
    async def _is_connection_alive(self, driver) -> bool:
        """检查连接是否存活"""
        try:
            loop = asyncio.get_event_loop()
            # 发送一个简单的命令检查连接
            await loop.run_in_executor(self.thread_pool, lambda: driver.current_url)
            return True
        except Exception:
            return False
    
    async def _wait_for_available_connection(self, serial_id: str) -> Optional[Any]:
        """等待可用连接"""
        max_wait_time = 30  # 最大等待30秒
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            connections = self.connections.get(serial_id, [])
            
            for conn_info in connections:
                if conn_info.status == ConnectionStatus.IDLE:
                    if await self._is_connection_alive(conn_info.driver):
                        conn_info.status = ConnectionStatus.BUSY
                        conn_info.last_used = time.time()
                        return conn_info.driver
            
            # 等待100ms后重试
            await asyncio.sleep(0.1)
        
        logger.error(f"等待连接超时: {serial_id}")
        return None
    
    async def _cleanup_idle_connections(self):
        """定期清理空闲连接"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                current_time = time.time()
                
                for serial_id in list(self.connections.keys()):
                    lock = self.connection_locks.get(serial_id)
                    if not lock:
                        continue
                    
                    async with lock:
                        connections = self.connections.get(serial_id, [])
                        # 清理超时的空闲连接
                        active_connections = []
                        
                        for conn_info in connections:
                            if conn_info.status == ConnectionStatus.IDLE:
                                if current_time - conn_info.last_used > self.max_idle_time:
                                    # 关闭超时连接
                                    try:
                                        await asyncio.get_event_loop().run_in_executor(
                                            self.thread_pool, 
                                            conn_info.driver.quit
                                        )
                                        logger.info(f"清理空闲连接: {serial_id}")
                                    except Exception as e:
                                        logger.error(f"清理连接失败: {serial_id}, {e}")
                                    continue
                            
                            active_connections.append(conn_info)
                        
                        if active_connections:
                            self.connections[serial_id] = active_connections
                        else:
                            # 没有活跃连接，清理整个设备记录
                            self.connections.pop(serial_id, None)
                            self.connection_locks.pop(serial_id, None)
                            
            except Exception as e:
                logger.error(f"清理连接任务异常: {e}") 