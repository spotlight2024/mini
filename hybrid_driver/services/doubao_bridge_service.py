"""桥接 Selenium 与 Playwright 的豆包搜索服务。"""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import AsyncIterator
from dataclasses import replace
from typing import Optional

from hybrid_driver.business_framework.business.doubao_business import DoubaoBusiness
from hybrid_driver.log_config import get_logger
from hybrid_driver.mcp.config import DoubaoMCPConfig
from hybrid_driver.mcp.doubao_playwright import DoubaoPlaywrightAutomation, DoubaoResult
from hybrid_driver.services.doubao_types import DoubaoChunk

LOGGER = get_logger(__name__)


class DoubaoBridgeService:
    """负责通过 Selenium 获取 CDP，再交给 Playwright 执行查询。"""

    def __init__(self, config: DoubaoMCPConfig) -> None:
        self._config = config
        self._business: Optional[DoubaoBusiness] = None
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # public api
    # ------------------------------------------------------------------
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
            self._handle_timeout(exc)
            raise TimeoutError("豆包查询超时") from exc
        finally:
            loop.close()
            self._release_business()

    async def stream_execute(self, query: str) -> AsyncIterator[DoubaoChunk]:
        """异步流式执行查询，逐个返回 DoubaoChunk。"""

        if not query or not query.strip():
            raise ValueError("query 不能为空")

        pw_config, cdp_endpoint = self._prepare_playwright_config()
        LOGGER.info(
            "[Bridge] 流式执行豆包查询，query_len=%d endpoint=%s",
            len(query),
            cdp_endpoint,
        )

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Optional[DoubaoChunk]] = asyncio.Queue()
        timeout = self._config.response_timeout
        automation_holder: dict[str, Optional[DoubaoPlaywrightAutomation]] = {"automation": None}
        cancelled = False

        def listener(chunk: DoubaoChunk) -> None:
            LOGGER.debug(
                "[Bridge] <- chunk seq=%s source=%s len=%d final=%s",
                chunk.sequence,
                chunk.source,
                len(chunk.delta),
                chunk.is_final,
            )
            loop.call_soon_threadsafe(queue.put_nowait, chunk)

        def worker() -> None:
            LOGGER.debug("[Bridge] worker thread started")
            try:
                with DoubaoPlaywrightAutomation(pw_config) as automation:
                    automation_holder["automation"] = automation
                    automation.add_chunk_listener(listener)
                    result = automation.search(query)
                LOGGER.info("[Bridge] Playwright 流式查询完成，answer_len=%d", len(result.answer_text or ""))
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("[Bridge] Playwright 流式查询失败")
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
                automation_holder["automation"] = None
                loop.call_soon_threadsafe(queue.put_nowait, None)
                LOGGER.debug("[Bridge] worker thread finished")

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
                    LOGGER.debug("[Bridge] queue received sentinel")
                    break
                yield chunk
                if chunk.is_final:
                    continue
        except asyncio.CancelledError:
            cancelled = True
            LOGGER.warning("[Bridge] 上游取消流式查询，开始清理资源")
            automation = automation_holder.get("automation")
            if automation is not None:
                automation.shutdown()
            raise
        except asyncio.TimeoutError as exc:
            self._handle_timeout(exc)
            automation = automation_holder.get("automation")
            if automation is not None:
                automation.shutdown()
            raise TimeoutError("豆包查询超时") from exc
        finally:
            worker_thread.join(timeout=1)
            if worker_thread.is_alive():
                LOGGER.warning("[Bridge] worker thread 未在预期时间内结束")
            self._release_business()
            if cancelled:
                LOGGER.debug("[Bridge] 流式查询已取消，资源释放完毕")

    def shutdown(self) -> None:
        with self._lock:
            if not self._business:
                return
            try:
                self._business.cleanup()
            finally:
                self._business = None

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
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
        metadata = {"base_url": self._config.base_url, "engine": "playwright"}
        return DoubaoResult(
            query=query,
            answer_text="\n".join(lines),
            answer_lines=lines,
            raw_text=answer_text,
            metadata=metadata,
        )

    def _prepare_playwright_config(self) -> tuple[DoubaoMCPConfig, str]:
        with self._lock:
            business = self._ensure_business()
            driver = business.get_driver()
            if driver is None:
                raise RuntimeError("Selenium driver 未成功创建")
            cdp_endpoint = self._get_cdp_endpoint(business)
        pw_config = replace(self._config, cdp_endpoint=cdp_endpoint)
        return pw_config, cdp_endpoint

    def _ensure_business(self) -> DoubaoBusiness:
        if self._business and self._business.get_driver() and self._config.reuse_session:
            return self._business
        if self._business and not self._config.reuse_session:
            try:
                self._business.cleanup()
            finally:
                self._business = None

        session_id = f"bridge-{threading.get_ident():x}"
        user_id = "bridge_doubao"
        overrides = {
            "hub_url": self._config.remote_url,
            "home_url": self._config.base_url,
        }
        business = DoubaoBusiness(session_id=session_id, user_id=user_id, site_overrides=overrides)
        options = business.get_chrome_options()
        for argument in self._config.chrome_arguments:
            options.add_argument(argument)
        if self._config.accept_insecure_certs:
            options.set_capability("acceptInsecureCerts", True)
        for key, value in self._config.remote_capabilities.items():
            options.set_capability(key, value)

        business.initialize().initialize_pages()
        if not business.open_home_page():
            business.cleanup()
            raise RuntimeError("豆包首页打开失败")

        driver = business.get_driver()
        if driver is None:
            business.cleanup()
            raise RuntimeError("豆包业务未返回有效 WebDriver")

        driver.implicitly_wait(0)
        driver.set_page_load_timeout(self._config.navigation_timeout)
        self._business = business
        return business

    def _get_cdp_endpoint(self, business: DoubaoBusiness) -> str:
        manager = getattr(business, "webdriver_manager", None)
        if manager is None or not hasattr(manager, "get_cdp_endpoint"):
            raise RuntimeError("webdriver_manager 未提供 get_cdp_endpoint")
        endpoint = manager.get_cdp_endpoint()  # type: ignore[call-arg]
        if not endpoint:
            raise RuntimeError("Selenium Grid 未暴露 se:cdp endpoint")
        rewritten = self._config.apply_cdp_override(endpoint)
        return rewritten or endpoint

    def _handle_timeout(self, exc: Exception | None = None) -> None:
        LOGGER.error("[Bridge] 豆包查询超时: %s", exc or "timeout")
        self._release_business()

    def _release_business(self) -> None:
        with self._lock:
            if not self._business:
                return
            try:
                self._business.cleanup()
            finally:
                self._business = None
