"""桥接 Selenium 与 Playwright 的豆包搜索服务。"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, replace
from typing import Optional

from hybrid_driver.business_framework.business.doubao_business import DoubaoBusiness
from hybrid_driver.log_config import get_logger
from hybrid_driver.doubao_mcp.config import DoubaoMCPConfig
from hybrid_driver.doubao_mcp.doubao_playwright import AutomationCancelled, DoubaoPlaywrightAutomation, DoubaoResult
from hybrid_driver.proxy.proxy_provider import get_proxy_config_for_selenium
from hybrid_driver.services.doubao_types import DoubaoChunk

LOGGER = get_logger(__name__)


@dataclass
class _BridgeSession:
    business: DoubaoBusiness
    cdp_endpoint: str


class DoubaoBridgeService:
    """负责通过 Selenium 获取 CDP，再交给 Playwright 执行查询。"""

    def __init__(self, config: DoubaoMCPConfig) -> None:
        self._config = config

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
            raise TimeoutError("豆包查询超时") from exc
        finally:
            loop.close()

    async def stream_execute(self, query: str) -> AsyncIterator[DoubaoChunk]:
        """异步流式执行查询，逐个返回 DoubaoChunk。"""

        if not query or not query.strip():
            raise ValueError("query 不能为空")

        session: _BridgeSession | None = None
        try:
            session = await asyncio.to_thread(self._create_session)
        except Exception:
            LOGGER.exception("[Bridge] 创建 DoubaoBusiness 失败")
            raise

        pw_config = replace(self._config, cdp_endpoint=session.cdp_endpoint)
        LOGGER.info(
            "[Bridge] 流式执行豆包查询，query_len={} endpoint={}",
            len(query),
            session.cdp_endpoint,
        )

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Optional[DoubaoChunk]] = asyncio.Queue()
        timeout = self._config.response_timeout
        cancel_event = threading.Event()
        cancelled = False

        def listener(chunk: DoubaoChunk) -> None:
            if cancel_event.is_set():
                return
            LOGGER.debug(
                "[Bridge] <- chunk seq={} source={} len={} final={}",
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
                    automation.add_chunk_listener(listener)
                    automation.set_cancel_checker(cancel_event.is_set)
                    result = automation.search(query)
                LOGGER.info("[Bridge] Playwright 流式查询完成，answer_len={}", len(result.answer_text or ""))
            except AutomationCancelled:
                LOGGER.info("[Bridge] Playwright 查询被上游取消")
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
            cancel_event.set()
            raise
        except asyncio.TimeoutError as exc:
            cancel_event.set()
            raise TimeoutError("豆包查询超时") from exc
        finally:
            cancel_event.set()
            worker_thread.join(timeout=1)
            if worker_thread.is_alive():
                LOGGER.warning("[Bridge] worker thread 未在预期时间内结束")
            await asyncio.to_thread(self._cleanup_session, session)
            if cancelled:
                LOGGER.debug("[Bridge] 流式查询已取消，资源释放完毕")

    def shutdown(self) -> None:
        """当前为按请求创建会话，暂无全局资源可释放。"""
        return

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

    def _get_cdp_endpoint(self, business: DoubaoBusiness) -> str:
        manager = getattr(business, "webdriver_manager", None)
        if manager is None or not hasattr(manager, "get_cdp_endpoint"):
            raise RuntimeError("webdriver_manager 未提供 get_cdp_endpoint")
        endpoint = manager.get_cdp_endpoint()  # type: ignore[call-arg]
        if not endpoint:
            raise RuntimeError("Selenium Grid 未暴露 se:cdp endpoint")
        rewritten = self._config.apply_cdp_override(endpoint)
        return rewritten or endpoint

    def _create_session(self) -> _BridgeSession:
        session_id = f"bridge-{uuid.uuid4().hex[:8]}"
        user_id = f"bridge_doubao_{session_id}"
        overrides = {
            "hub_url": self._config.remote_url,
            "home_url": self._config.base_url,
        }
        business = DoubaoBusiness(session_id=session_id, user_id=user_id, site_overrides=overrides)
        options = business.get_chrome_options()
        proxy_provider = (self._config.proxy_provider or "").strip()
        if proxy_provider:
            LOGGER.info("[Bridge] 准备获取代理配置，provider= {}", proxy_provider)
            proxy_config = None
            try:
                proxy_config = get_proxy_config_for_selenium(proxy_provider)
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("[Bridge] 获取代理配置失败，改用直连: %s", exc)
            if proxy_config:
                LOGGER.info(
                    "[Bridge] 使用代理 %s:%s（provider=%s）",
                    proxy_config.get("ip"),
                    proxy_config.get("port"),
                    proxy_config.get("username"),
                    proxy_config.get("password"),
                    proxy_provider,
                )
                options.set_capability("se:proxyConfig", proxy_config)
            else:
                LOGGER.warning("[Bridge] 未获取到代理配置，改用直连")
        for argument in self._config.chrome_arguments:
            options.add_argument(argument)
        if self._config.accept_insecure_certs:
            options.set_capability("acceptInsecureCerts", True)
        for key, value in self._config.remote_capabilities.items():
            options.set_capability(key, value)

        business.initialize()
        business.initialize_pages()
        # if not business.open_home_page():
        #     business.cleanup()
        #     raise RuntimeError("豆包首页打开失败")


        driver = business.get_driver()
        if driver is None:
            business.cleanup()
            raise RuntimeError("豆包业务未返回有效 WebDriver")

        driver.implicitly_wait(0)
        driver.set_page_load_timeout(self._config.navigation_timeout)
        cdp_endpoint = self._get_cdp_endpoint(business)
        return _BridgeSession(business=business, cdp_endpoint=cdp_endpoint)

    def _cleanup_session(self, session: Optional[_BridgeSession]) -> None:
        if not session:
            return
        try:
            session.business.cleanup()
        except Exception:  # noqa: BLE001
            LOGGER.warning("[Bridge] 清理业务会话失败", exc_info=True)
