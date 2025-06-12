import threading
import time
from collections import OrderedDict

class WebDriverPool:
    def __init__(self, driver_cls, max_size=10, idle_timeout=1800):
        self.driver_cls = driver_cls
        self.max_size = max_size
        self.idle_timeout = idle_timeout
        self.pool = OrderedDict()  # serial_id -> (driver, last_active_time)
        self.lock = threading.Lock()
        self.stats = {
            "get_count": 0,
            "release_count": 0,
            "cleanup_count": 0,
            "fail_count": 0,
        }

    def get(self, serial_id, retry=2):
        with self.lock:
            self.stats["get_count"] += 1
            entry = self.pool.get(serial_id)
            driver = None
            if entry:
                driver, _ = entry
                if not self.is_driver_healthy(driver):
                    self.release(serial_id)
                    driver = None
            if not driver:
                for _ in range(retry):
                    try:
                        driver = self.driver_cls()
                        driver.connect(serial_id)
                        break
                    except Exception:
                        driver = None
                        continue
                if not driver:
                    self.stats["fail_count"] += 1
                    raise RuntimeError(f"Failed to get healthy WebDriver for {serial_id}")
                # LRU淘汰
                if len(self.pool) >= self.max_size:
                    self._evict_lru()
            self.pool[serial_id] = (driver, time.time())
            self.pool.move_to_end(serial_id)
            return driver

    def release(self, serial_id):
        with self.lock:
            self.stats["release_count"] += 1
            entry = self.pool.pop(serial_id, None)
            if entry:
                driver, _ = entry
                try:
                    driver.quit()
                except Exception:
                    pass

    def cleanup(self):
        with self.lock:
            now = time.time()
            to_remove = []
            for serial_id, (driver, last_active) in list(self.pool.items()):
                if now - last_active > self.idle_timeout or not self.is_driver_healthy(driver):
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    to_remove.append(serial_id)
            for serial_id in to_remove:
                del self.pool[serial_id]
            self.stats["cleanup_count"] += len(to_remove)

    def _evict_lru(self):
        # 淘汰最久未用的driver
        if self.pool:
            serial_id, (driver, _) = next(iter(self.pool.items()))
            try:
                driver.quit()
            except Exception:
                pass
            del self.pool[serial_id]

    def is_driver_healthy(self, driver):
        try:
            # 可自定义健康检查逻辑
            return hasattr(driver, "session_id") and driver.session_id is not None
        except Exception:
            return False

    def stats_info(self):
        with self.lock:
            return dict(self.stats, pool_size=len(self.pool))

    # 上下文管理支持
    class Session:
        def __init__(self, pool, serial_id):
            self.pool = pool
            self.serial_id = serial_id
            self.driver = None
        def __enter__(self):
            self.driver = self.pool.get(self.serial_id)
            return self.driver
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.pool.release(self.serial_id)

    def session(self, serial_id):
        return WebDriverPool.Session(self, serial_id) 