"""
Selenium implementation for automating Doubao chat.
"""

from __future__ import annotations

import random
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from difflib import SequenceMatcher

from selenium.common.exceptions import TimeoutException as SeleniumTimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from hybrid_driver.business_framework.business.doubao_business import DoubaoBusiness
from hybrid_driver.business_framework.core.action_chains_wrapper import ActionChainsWrapper
from hybrid_driver.business_framework.core.webdriver_chain import WebDriverChain
from hybrid_driver.log_config import get_logger
from hybrid_driver.mcp.config import DoubaoMCPConfig
from hybrid_driver.proxy.proxy_provider import get_proxy_config_for_selenium
from hybrid_driver.services.doubao_types import DoubaoChunk, StreamSource

from .doubao_playwright import AutomationCancelled, DoubaoResult, _is_static_text, _normalize_text, _STATIC_TOKENS
def _compute_text_diff(previous: str, current: str) -> tuple[List[str], bool]:
    matcher = SequenceMatcher(a=previous, b=current, autojunk=False)
    chunks: List[str] = []
    had_deletion = False
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":
            had_deletion = True
            continue
        if tag in {"insert", "replace"}:
            snippet = current[j1:j2]
            if snippet:
                chunks.append(snippet)
    return chunks, had_deletion

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class _SeleniumSession:
    business: DoubaoBusiness
    driver: WebDriver
    session_id: str
    actions: ActionChainsWrapper
    chain: WebDriverChain


class DoubaoSeleniumAutomation:
    """Uses Selenium to automate Doubao with the same interface as the Playwright automation."""

    def __init__(self, config: DoubaoMCPConfig) -> None:
        self._config = config
        self._session: Optional[_SeleniumSession] = None
        self._chunk_listeners: list[Callable[[DoubaoChunk], None]] = []
        self._should_cancel: Callable[[], bool] = lambda: False
        self._stream_sequence = 0
        self._last_full_text = ""
        self._session_lock = threading.RLock()

    # ------------------------------------------------------------------
    # context manager helpers
    # ------------------------------------------------------------------
    def __enter__(self) -> "DoubaoSeleniumAutomation":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401 - context manager cleanup
        self.shutdown()

    def close(self) -> None:
        """Alias for shutdown() to align with expected interfaces."""

        self.shutdown()

    # ------------------------------------------------------------------
    # public helpers
    # ------------------------------------------------------------------
    def add_chunk_listener(self, listener: Callable[[DoubaoChunk], None]) -> None:
        """Register a listener to receive incremental chunks."""

        self._chunk_listeners.append(listener)

    def set_cancel_checker(self, checker: Callable[[], bool]) -> None:
        """Install a callable that returns True when the automation should cancel."""

        self._should_cancel = checker

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _reset_stream_state(self) -> None:
        self._stream_sequence = 0
        self._last_full_text = ""

    def _check_cancelled(self) -> None:
        if self._should_cancel():
            raise AutomationCancelled("automation cancelled by upstream request")

    def _emit_chunk(
        self,
        *,
        delta: str,
        full_text: str,
        source: StreamSource,
        is_final: bool,
        metadata: Optional[Dict[str, object]] = None,
    ) -> None:
        if not self._chunk_listeners:
            return
        self._stream_sequence += 1
        chunk = DoubaoChunk(
            delta=delta,
            full_text=full_text,
            source=source,
            sequence=self._stream_sequence,
            is_final=is_final,
            timestamp=time.time(),
            metadata=(metadata or {}).copy(),
        )
        for listener in list(self._chunk_listeners):
            try:
                listener(chunk)
            except Exception:  # pragma: no cover - defensive logging
                LOGGER.exception("chunk listener failed")

    def _emit_text_update(self, new_text: str, source: StreamSource) -> None:
        if not new_text:
            return
        if self._chunk_listeners:
            if new_text == self._last_full_text:
                return
            if new_text.startswith(self._last_full_text):
                delta = new_text[len(self._last_full_text) :]
            else:
                delta = new_text
            self._emit_chunk(delta=delta, full_text=new_text, source=source, is_final=False)
        self._last_full_text = new_text

    def _emit_error(self, message: str) -> None:
        if not self._chunk_listeners:
            return
        self._emit_chunk(
            delta="",
            full_text=self._last_full_text,
            source="error",
            is_final=True,
            metadata={"error": message},
        )

    def _ensure_session(self) -> _SeleniumSession:
        with self._session_lock:
            if self._session and self._config.reuse_session:
                try:
                    self._session.driver.current_url  # probe session validity
                    return self._session
                except WebDriverException:
                    LOGGER.warning("Existing Selenium session unavailable，重新创建")
                    self._destroy_session()

            if self._session:
                return self._session

            session_id = f"selenium-{uuid.uuid4().hex[:8]}"
            user_id = f"selenium_doubao_{session_id}"
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

            proxy_provider = (self._config.proxy_provider or "").strip()
            if proxy_provider:
                LOGGER.info("[Selenium] 准备获取代理配置，provider={}", proxy_provider)
                proxy_config = None
                try:
                    proxy_config = get_proxy_config_for_selenium(proxy_provider)
                except Exception as exc:  # noqa: BLE001
                    LOGGER.warning("[Selenium] 获取代理配置失败，改用直连: %s", exc)
                if proxy_config:
                    LOGGER.info(
                        "[Selenium] 使用代理 %s:%s（provider=%s）",
                        proxy_config.get("ip"),
                        proxy_config.get("port"),
                        proxy_config.get("provider"),
                    )
                    options.set_capability("se:proxyConfig", proxy_config)
                else:
                    LOGGER.warning("[Selenium] 未获取到代理配置，改用直连")

            business.initialize()
            business.initialize_pages()

            driver = business.get_driver()
            if driver is None:
                business.cleanup()
                raise RuntimeError("豆包业务未返回有效 WebDriver")

            driver.implicitly_wait(0)
            driver.set_page_load_timeout(self._config.navigation_timeout)

            actions = business.get_action_chains()
            chain = business.get_webdriver_chain()
            if actions is None or chain is None:
                business.cleanup()
                raise RuntimeError("豆包业务未初始化 ActionChains 或 WebDriverChain")
            try:
                actions.enable_human_actions()
            except Exception:  # noqa: BLE001
                LOGGER.debug("[Selenium] 启用人类化行为失败，保持默认动作链", exc_info=True)
            actions.reset_actions()

            self._session = _SeleniumSession(
                business=business,
                driver=driver,
                session_id=session_id,
                actions=actions,
                chain=chain,
            )
            return self._session

    def _destroy_session(self) -> None:
        with self._session_lock:
            if not self._session:
                return
            try:
                self._session.actions.reset_actions()
                self._session.business.cleanup()
            except Exception:  # noqa: BLE001
                LOGGER.warning("[Selenium] 清理业务会话失败", exc_info=True)
            finally:
                self._session = None

    def _navigate(self, session: _SeleniumSession) -> None:
        self._check_cancelled()
        LOGGER.info("[Selenium] Navigating to Doubao: {}", self._config.base_url)
        session.chain.navigate_to(self._config.base_url)
        WebDriverWait(session.driver, self._config.navigation_timeout).until(
            lambda d: "doubao" in (d.current_url or "").lower()
        )
        self._human_pause()

    def _input_query(self, session: _SeleniumSession, query: str) -> None:
        self._check_cancelled()
        LOGGER.info("[Selenium] Filling query = {}", query)
        chain = session.chain
        actions = session.actions.reset_actions()
        locator = (By.CSS_SELECTOR, self._config.input_selector)
        try:
            input_box = chain.wait_for_element(
                locator[0],
                locator[1],
                timeout=int(self._config.navigation_timeout),
                description="豆包输入框",
            )
            chain.wait_for_clickable(locator[0], locator[1], timeout=int(self._config.navigation_timeout))
        except SeleniumTimeoutException as exc:
            raise TimeoutError("未定位到豆包输入框") from exc

        try:
            actions.move_to_element(locator[0], locator[1], "豆包输入框").click(locator[0], locator[1], "豆包输入框").perform()
        except Exception:  # noqa: BLE001
            LOGGER.debug("[Selenium] ActionChains 点击输入框失败，退回原生 click", exc_info=True)
            input_box.click()
        self._human_pause(0.2, 0.5)

        try:
            input_box.clear()
        except Exception:  # noqa: BLE001
            session.driver.execute_script("arguments[0].value='';", input_box)

        actions.reset_actions()
        try:
            actions.send_keys(query, locator[0], locator[1], "豆包输入框").perform()
        except Exception:  # noqa: BLE001
            LOGGER.debug("[Selenium] ActionChains 输入失败，退回原生 send_keys", exc_info=True)
            input_box.send_keys(query)

        send_button_selector = "[data-testid='chat_input_send_button']"
        try:
            chain.wait_for_clickable(By.CSS_SELECTOR, send_button_selector, timeout=5, description="发送按钮")
            actions.reset_actions()
            actions.move_to_element(By.CSS_SELECTOR, send_button_selector, "发送按钮").click(
                By.CSS_SELECTOR, send_button_selector, "发送按钮"
            ).perform()
            self._human_pause(0.3, 0.7)
        except SeleniumTimeoutException:
            LOGGER.warning("[Selenium] 发送按钮不可点击，尝试执行 JS 点击")
            session.driver.execute_script(
                "const btn = document.querySelector(arguments[0]); if (btn) { btn.click(); }",
                send_button_selector,
            )

    def _wait_for_answer(self, driver: WebDriver) -> Dict[str, object]:
        timeout_at = time.time() + self._config.response_timeout
        dom_previous_text = ""
        dom_last_cleaned = ""
        dom_stable_runs = 0

        while time.time() < timeout_at:
            self._check_cancelled()
            dom_snapshot = self._read_answer_from_dom(driver)
            if dom_snapshot:
                current_text = dom_snapshot.get("text") or ""
                if current_text and current_text != dom_previous_text:
                    chunks, had_deletion = _compute_text_diff(dom_previous_text, current_text)
                    dom_previous_text = current_text
                    if chunks:
                        for chunk in chunks:
                            preview = chunk.replace("\n", " ").strip()
                            if len(preview) > 120:
                                preview = f"{preview[:120]}..."
                            LOGGER.debug("[Selenium] DOM chunk += len={} preview={}", len(chunk), preview)
                    elif had_deletion:
                        LOGGER.debug("[Selenium] DOM 文本发生删除或重排，等待后续片段")
                    else:
                        LOGGER.debug("[Selenium] DOM 文本更新但未检测到新增 chunk")

                if dom_snapshot.get("streaming"):
                    dom_stable_runs = 0
                else:
                    cleaned = dom_snapshot.get("cleaned", "")
                    if cleaned == dom_last_cleaned:
                        dom_stable_runs += 1
                    else:
                        dom_last_cleaned = cleaned
                        dom_stable_runs = 0
                    if dom_stable_runs >= 2:
                        LOGGER.info("[Selenium] DOM 回答稳定，返回长度={}", len(dom_snapshot.get("cleaned", "")))
                        return dom_snapshot
            time.sleep(self._config.poll_interval)

        raise TimeoutError("等待豆包 DOM 回应超时")

    def _read_answer_from_dom(self, driver: WebDriver) -> Optional[Dict[str, object]]:
        self._check_cancelled()
        script = """
            const trim = (text) => (text || '').replace(/\\u200b/g, '').trim();
            const blocks = Array.from(
                document.querySelectorAll('[data-testid="message-block-container"]')
            );
            for (let i = blocks.length - 1; i >= 0; i -= 1) {
                const block = blocks[i];
                if (block.querySelector('[data-testid="send_message"]')) continue;
                const textNode = block.querySelector('[data-testid="message_text_content"]');
                const text = trim(textNode ? textNode.innerText : block.innerText);
                const streaming = (block.getAttribute('data-stream-state') || block.dataset.streamState || '').toLowerCase();
                if (!text) continue;
                if (arguments[0].includes(text)) continue;
                if (/^找到\\s*\\d+\\s*篇资料参考$/.test(text)) continue;
                return { text, streaming };
            }
            return null;
        """
        try:
            result = driver.execute_script(script, list(_STATIC_TOKENS))
        except WebDriverException:
            return None

        self._check_cancelled()
        if not result:
            return None
        text = result.get("text", "")
        cleaned = _normalize_text(text)
        if not cleaned or _is_static_text(cleaned):
            return None
        streaming = str(result.get("streaming", "") or "").lower() in {"loading", "pending", "streaming"}
        full_text = text.strip()
        self._emit_text_update(full_text, "dom")
        return {"text": full_text, "cleaned": cleaned, "streaming": streaming}

    # ------------------------------------------------------------------
    # public api
    # ------------------------------------------------------------------
    def search(self, query: str) -> DoubaoResult:
        if not query or not query.strip():
            raise ValueError("query 不能为空")

        self._reset_stream_state()
        self._check_cancelled()
        session = self._ensure_session()
        driver = session.driver
        self._check_cancelled()
        self._navigate(session)
        self._check_cancelled()
        self._input_query(session, query)
        self._check_cancelled()
        try:
            response = self._wait_for_answer(driver)
        except AutomationCancelled:
            raise
        except Exception as exc:
            self._emit_error(str(exc))
            raise

        text = response.get("text", "")
        self._emit_text_update(text, "dom")
        self._last_full_text = text
        self._emit_chunk(
            delta="",
            full_text=text,
            source="final",
            is_final=True,
            metadata={"base_url": self._config.base_url, "engine": "selenium"},
        )

        answer_lines = [
            line for line in text.splitlines() if line.strip() and not _is_static_text(_normalize_text(line))
        ]
        if not answer_lines:
            answer_lines = [text]

        return DoubaoResult(
            query=query,
            answer_text="\n".join(answer_lines),
            answer_lines=answer_lines,
            raw_text=text,
            metadata={"base_url": self._config.base_url, "engine": "selenium"},
        )

    def shutdown(self) -> None:
        """Gracefully close Selenium resources."""

        self._destroy_session()

    @staticmethod
    def _human_pause(min_seconds: float = 0.15, max_seconds: float = 0.35) -> None:
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)


