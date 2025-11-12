"""豆包搜索流式服务封装。

该模块提供面向上层的统一异步接口，屏蔽底层 Selenium/CDP 或 Playwright
自动化差异，使调用方可以通过异步生成器逐步获取回答分片。
"""

from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator

from hybrid_driver.log_config import get_logger
from hybrid_driver.mcp.config import DoubaoMCPConfig
from hybrid_driver.mcp.doubao_playwright import DoubaoResult
from hybrid_driver.services.doubao_bridge_service import DoubaoBridgeService
from hybrid_driver.services.doubao_types import DoubaoChunk

LOGGER = get_logger(__name__)


class DoubaoStreamService:
    """提供豆包搜索的异步流式查询接口。"""

    def __init__(
        self,
        config: DoubaoMCPConfig,
    ) -> None:
        self._config = config
        self._bridge = DoubaoBridgeService(config)
        self._shutdown_lock = asyncio.Lock()

    async def stream_search(
        self,
        query: str,
    ) -> AsyncIterator[DoubaoChunk]:
        """异步执行搜索并逐步返回回答分片。

        基于桥接服务实时获取 Playwright 产生的增量文本，并包装为 DoubaoChunk。
        """

        if not query or not query.strip():
            raise ValueError("searchContent 不能为空")

        LOGGER.info("启动豆包搜索: query_len=%d", len(query))
        start_time = time.time()
        try:
            async for chunk in self._bridge.stream_execute(query):
                yield chunk
                if chunk.is_final:
                    LOGGER.info(
                        "豆包搜索完成: answer_len=%d duration=%.2fs",
                        len(chunk.full_text),
                        time.time() - start_time,
                    )
        except TimeoutError as exc:
            LOGGER.warning("豆包搜索超时: %s", exc)
            raise
        except asyncio.CancelledError:
            LOGGER.warning("豆包搜索被上游取消")
            raise

    async def search(
        self,
        query: str,
    ) -> DoubaoResult:
        """执行搜索并返回完整结果。"""

        if not query or not query.strip():
            raise ValueError("searchContent 不能为空")

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, self._bridge.execute, query)
        except TimeoutError as exc:
            LOGGER.warning("豆包搜索超时: %s", exc)
            raise

    async def shutdown(self) -> None:
        """关闭底层自动化资源。"""

        async with self._shutdown_lock:
            await asyncio.to_thread(self._bridge.shutdown)
