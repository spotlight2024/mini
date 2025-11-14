"""Selenium-based Doubao search service with stream support."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import AsyncIterator, Optional

from hybrid_driver.log_config import get_logger
from hybrid_driver.doubao_mcp.config import DoubaoMCPConfig
from hybrid_driver.doubao_mcp.doubao_playwright import AutomationCancelled, DoubaoResult
from hybrid_driver.doubao_mcp.doubao_selenium import DoubaoSeleniumAutomation
from hybrid_driver.services.doubao_types import DoubaoChunk

LOGGER = get_logger(__name__)


class DoubaoSeleniumService:
    """负责通过 Selenium 直接执行豆包查询并支持流式输出。"""

    def __init__(self, config: DoubaoMCPConfig) -> None:
        self._config = config

    def execute(self, query: str) -> DoubaoResult:
        """执行单次查询并返回豆包结果。"""

        if not query or not query.strip():
            raise ValueError("query 不能为空")

        async def _collect() -> DoubaoResult:
            chunks: list[DoubaoChunk] = []
            async for chunk in self.stream_execute(query):
                chunks.append(chunk)
                if chunk.is_final:
                    break
            return self._chunks_to_result(query, chunks)

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(asyncio.wait_for(_collect(), self._config.response_timeout))
        except asyncio.TimeoutError as exc:
            raise TimeoutError("豆包查询超时") from exc
        finally:
            loop.close()

    async def stream_execute(self, query: str) -> AsyncIterator[DoubaoChunk]:
        """异步流式执行查询，逐个返回 DoubaoChunk。"""

        if not query or not query.strip():
            raise ValueError("query 不能为空")

        LOGGER.info("[SeleniumService] 流式执行豆包查询，query_len={}", len(query))

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Optional[DoubaoChunk]] = asyncio.Queue()
        timeout = self._config.response_timeout
        cancel_event = threading.Event()
        cancelled = False

        def listener(chunk: DoubaoChunk) -> None:
            if cancel_event.is_set():
                return
            LOGGER.debug(
                "[SeleniumService] <- chunk seq={} source={} len={} final={}",
                chunk.sequence,
                chunk.source,
                len(chunk.delta),
                chunk.is_final,
            )
            loop.call_soon_threadsafe(queue.put_nowait, chunk)

        def worker() -> None:
            LOGGER.debug("[SeleniumService] worker thread started")
            try:
                with DoubaoSeleniumAutomation(self._config) as automation:
                    automation.add_chunk_listener(listener)
                    automation.set_cancel_checker(cancel_event.is_set)
                    result = automation.search(query)
                LOGGER.info(
                    "[SeleniumService] Selenium 查询完成，answer_len={}",
                    len(result.answer_text or ""),
                )
            except AutomationCancelled:
                LOGGER.info("[SeleniumService] Selenium 查询被上游取消")
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("[SeleniumService] Selenium 查询失败")
                error_chunk = DoubaoChunk(
                    delta="",
                    full_text="",
                    source="error",
                    sequence=-1,
                    is_final=True,
                    timestamp=time.time(),
                    metadata={"error": str(exc)},
                )
                loop.call_soon_threadsafe(queue.put_nowait, error_chunk)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)
                LOGGER.debug("[SeleniumService] worker thread finished")

        worker_thread = threading.Thread(target=worker, daemon=True)
        worker_thread.start()

        start = time.time()
        try:
            while True:
                remaining = timeout - (time.time() - start)
                if remaining <= 0:
                    raise asyncio.TimeoutError
                try:
                    chunk = await asyncio.wait_for(queue.get(), remaining)
                except asyncio.TimeoutError:
                    raise
                if chunk is None:
                    LOGGER.debug("[SeleniumService] queue received sentinel")
                    break
                yield chunk
                if chunk.is_final:
                    continue
        except asyncio.CancelledError:
            cancelled = True
            LOGGER.warning("[SeleniumService] 上游取消流式查询，开始清理资源")
            cancel_event.set()
            raise
        except asyncio.TimeoutError as exc:
            cancel_event.set()
            raise TimeoutError("豆包查询超时") from exc
        finally:
            cancel_event.set()
            worker_thread.join(timeout=1)
            if worker_thread.is_alive():
                LOGGER.warning("[SeleniumService] worker thread 未在预期时间内结束")
            if cancelled:
                LOGGER.debug("[SeleniumService] 流式查询已取消，资源释放完毕")

    def shutdown(self) -> None:
        """当前为按请求创建会话，暂无全局资源可释放。"""
        return

    def _chunks_to_result(self, query: str, chunks: list[DoubaoChunk]) -> DoubaoResult:
        if not chunks:
            raise RuntimeError("未获取到豆包回答")
        final = chunks[-1]
        if final.source == "error":
            raise RuntimeError(str((final.metadata or {}).get("error", "豆包查询失败")))
        answer_text = final.full_text
        lines = [line for line in answer_text.splitlines() if line.strip()]
        if not lines:
            lines = [answer_text]
        metadata = {"base_url": self._config.base_url, "engine": "selenium"}
        return DoubaoResult(
            query=query,
            answer_text="\n".join(lines),
            answer_lines=lines,
            raw_text=answer_text,
            metadata=metadata,
        )


