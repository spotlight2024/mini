"""豆包搜索流式服务封装。

该模块提供面向上层的统一异步接口，屏蔽底层 Selenium/CDP 或 Playwright
自动化差异，使调用方可以通过异步生成器逐步获取回答分片。
"""

from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator, Optional

from hybrid_driver.log_config import get_logger
from hybrid_driver.mcp.config import DoubaoMCPConfig
from hybrid_driver.mcp.doubao_playwright import DoubaoResult
from hybrid_driver.services.doubao_bridge_service import DoubaoBridgeService
from hybrid_driver.services.doubao_selenium_service import DoubaoSeleniumService
from hybrid_driver.services.doubao_types import DoubaoChunk

LOGGER = get_logger(__name__)

ENGINE_PLAYWRIGHT = "playwright"
ENGINE_SELENIUM = "selenium"
_SUPPORTED_ENGINES = {ENGINE_PLAYWRIGHT, ENGINE_SELENIUM}


class DoubaoStreamService:
    """提供豆包搜索的异步流式查询接口。"""

    def __init__(
        self,
        config: DoubaoMCPConfig,
    ) -> None:
        self._config = config
        self._bridge = DoubaoBridgeService(config)
        self._selenium = DoubaoSeleniumService(config)
        self._shutdown_lock = asyncio.Lock()
        self._max_concurrency = max(1, config.max_concurrent_sessions)
        self._loop_semaphores: dict[int, asyncio.Semaphore] = {}
        self._default_engine = self._normalize_engine(getattr(config, "default_engine", None))

    async def stream_search(
        self,
        query: str,
        *,
        engine: Optional[str] = None,
    ) -> AsyncIterator[DoubaoChunk]:
        """异步执行搜索并逐步返回回答分片。

        基于桥接服务实时获取 Playwright 产生的增量文本，并包装为 DoubaoChunk。
        """

        if not query or not query.strip():
            raise ValueError("searchContent 不能为空")

        resolved_engine = self._resolve_engine(engine)
        semaphore = self._get_loop_semaphore()
        await semaphore.acquire()
        LOGGER.info("启动豆包搜索: query_len={} engine={}", len(query), resolved_engine)
        start_time = time.time()

        if resolved_engine == ENGINE_PLAYWRIGHT:
            stream = self._bridge.stream_execute(query)
        else:
            stream = self._selenium.stream_execute(query)

        try:
            async for chunk in stream:
                yield chunk
                if chunk.is_final:
                    LOGGER.info(
                        "豆包搜索完成: answer_len={} duration={:.2f}s engine={}",
                        len(chunk.full_text),
                        time.time() - start_time,
                        resolved_engine,
                    )
        except TimeoutError as exc:
            LOGGER.warning("豆包搜索超时: {}", exc)
            raise
        except asyncio.CancelledError:
            LOGGER.warning("豆包搜索被上游取消")
            raise
        finally:
            semaphore.release()

    async def search(
        self,
        query: str,
        *,
        engine: Optional[str] = None,
    ) -> DoubaoResult:
        """执行搜索并返回完整结果。"""

        if not query or not query.strip():
            raise ValueError("searchContent 不能为空")

        resolved_engine = self._resolve_engine(engine)
        semaphore = self._get_loop_semaphore()
        await semaphore.acquire()
        loop = asyncio.get_running_loop()
        try:
            if resolved_engine == ENGINE_PLAYWRIGHT:
                return await loop.run_in_executor(None, self._bridge.execute, query)
            return await loop.run_in_executor(None, self._selenium.execute, query)
        except TimeoutError as exc:
            LOGGER.warning("豆包搜索超时: {}", exc)
            raise
        finally:
            semaphore.release()

    async def shutdown(self) -> None:
        """关闭底层自动化资源。"""

        async with self._shutdown_lock:
            await asyncio.to_thread(self._bridge.shutdown)
            await asyncio.to_thread(self._selenium.shutdown)

    def _get_loop_semaphore(self) -> asyncio.Semaphore:
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
        semaphore = self._loop_semaphores.get(loop_id)
        if semaphore is None:
            semaphore = asyncio.Semaphore(self._max_concurrency)
            self._loop_semaphores[loop_id] = semaphore
        return semaphore

    def _resolve_engine(self, engine: Optional[str]) -> str:
        candidate = self._normalize_engine(engine or self._default_engine)
        return candidate

    @staticmethod
    def _normalize_engine(engine: Optional[str]) -> str:
        candidate = (engine or ENGINE_PLAYWRIGHT).strip().lower()
        if candidate not in _SUPPORTED_ENGINES:
            raise ValueError(f"engine 参数无效，支持的引擎: {sorted(_SUPPORTED_ENGINES)}")
        return candidate

    @property
    def default_engine(self) -> str:
        return self._default_engine
