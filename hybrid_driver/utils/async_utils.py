import asyncio
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=100)  # 支持高并发

def run_sync(func, *args, **kwargs):
    """
    将同步函数转为异步（线程池），用于在 async 接口中安全调用阻塞型代码。
    """
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_executor, lambda: func(*args, **kwargs)) 