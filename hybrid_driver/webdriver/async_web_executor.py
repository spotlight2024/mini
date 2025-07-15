import asyncio
import time
from typing import Optional, List, Any, Dict
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By

from hybrid_driver.webdriver.connection_pool import WebDriverConnectionPool
from hybrid_driver.log_config import get_logger

logger = get_logger(__name__)

class AsyncWebExecutor:
    """异步 WebDriver 执行器 - 优化网络 I/O 性能"""
    
    def __init__(self, connection_pool: WebDriverConnectionPool):
        self.connection_pool = connection_pool
        self.thread_pool = ThreadPoolExecutor(max_workers=100)
        self.operation_cache: Dict[str, Any] = {}  # 操作结果缓存
        self.cache_ttl = 5  # 缓存5秒
        
    async def execute_with_connection(self, serial_id: str, operation_func, create_connection_func):
        """使用连接池执行操作"""
        driver = None
        try:
            # 从连接池获取连接
            driver = await self.connection_pool.get_connection(serial_id, create_connection_func)
            if not driver:
                raise Exception(f"无法获取连接: {serial_id}")
            
            # 执行操作
            result = await self._execute_operation_async(operation_func, driver)
            return result
            
        except Exception as e:
            logger.error(f"执行操作失败: {serial_id}, {e}")
            raise
        finally:
            # 释放连接回池
            if driver:
                await self.connection_pool.release_connection(serial_id, driver)
    
    async def _execute_operation_async(self, operation_func, driver) -> Any:
        """异步执行操作"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, operation_func, driver)
    
    async def find_element_with_cache(self, serial_id: str, by: str, value: str, 
                                    create_connection_func, timeout: int = 10) -> Optional[WebElement]:
        """带缓存的元素查找 - 减少重复查找"""
        cache_key = f"{serial_id}:{by}:{value}"
        
        # 检查缓存
        if cache_key in self.operation_cache:
            cache_entry = self.operation_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                logger.debug(f"使用缓存结果: {cache_key}")
                return cache_entry['result']
        
        # 执行查找
        def find_operation(driver):
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                return element
            except Exception as e:
                logger.error(f"查找元素失败: {by}={value}, {e}")
                return None
        
        result = await self.execute_with_connection(serial_id, find_operation, create_connection_func)
        
        # 缓存结果
        if result:
            self.operation_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
        
        return result
    
    async def batch_operations(self, serial_id: str, operations: List[Dict], 
                             create_connection_func) -> List[Any]:
        """批量执行操作 - 减少连接开销"""
        driver = None
        try:
            # 获取连接
            driver = await self.connection_pool.get_connection(serial_id, create_connection_func)
            if not driver:
                raise Exception(f"无法获取连接: {serial_id}")
            
            results = []
            for operation in operations:
                try:
                    op_type = operation['type']
                    if op_type == 'find_element':
                        result = await self._execute_operation_async(
                            lambda d: d.find_element(operation['by'], operation['value']), 
                            driver
                        )
                    elif op_type == 'click':
                        result = await self._execute_operation_async(
                            lambda d: d.find_element(operation['by'], operation['value']).click(), 
                            driver
                        )
                    elif op_type == 'get_url':
                        result = await self._execute_operation_async(
                            lambda d: d.current_url, 
                            driver
                        )
                    else:
                        result = None
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"批量操作失败: {operation}, {e}")
                    results.append(None)
            
            return results
            
        finally:
            if driver:
                await self.connection_pool.release_connection(serial_id, driver)
    
    async def parallel_operations(self, operations: List[Dict]) -> List[Any]:
        """并行执行多个设备的操作"""
        tasks = []
        for operation in operations:
            serial_id = operation['serial_id']
            op_func = operation['operation_func']
            create_func = operation['create_connection_func']
            
            task = asyncio.create_task(
                self.execute_with_connection(serial_id, op_func, create_func)
            )
            tasks.append(task)
        
        # 等待所有操作完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    def clear_cache(self, serial_id: Optional[str] = None):
        """清理缓存"""
        if serial_id:
            # 清理特定设备的缓存
            keys_to_remove = [k for k in self.operation_cache.keys() if k.startswith(f"{serial_id}:")]
            for key in keys_to_remove:
                self.operation_cache.pop(key, None)
        else:
            # 清理所有缓存
            self.operation_cache.clear() 