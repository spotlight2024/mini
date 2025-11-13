"""
Playwright implementation for automating Doubao chat.
"""

from __future__ import annotations

import os
import re
import time
from difflib import SequenceMatcher
import json
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Optional

from hybrid_driver.log_config import get_logger
from hybrid_driver.services.doubao_types import DoubaoChunk, StreamSource


from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Request, Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync


from .config import DoubaoMCPConfig

LOGGER = get_logger(__name__)
_COMPLETION_URL_PREFIX = "https://www.doubao.com/samantha/chat/completion"
_MESSAGE_ID_RE = re.compile(r'"message_id"\s*:\s*"([^"]+)"')

_STATIC_TOKENS = {
    "你好，我是豆包",
    "图像生成",
    "帮我写作",
    "翻译",
    "编程",
    "深入研究",
    "AI 播客",
    "记录会议",
    "音乐生成",
    "解题答疑",
    "更多",
    "问问豆包 · 划词提问 · 截图问答 · 网页速读",
    "下载豆包电脑版",
    "京ICP备2023020373号-1",
    "深度思考",
    "技能",
    "内容由 AI 生成",
    "登录",
    "正在搜索",
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _is_static_text(text: str) -> bool:
    normalized = _normalize_text(text)
    if not normalized:
        return True
    if normalized in _STATIC_TOKENS:
        return True
    if re.match(r"^找到\s*\d+\s*篇资料参考$", normalized):
        return True
    return False


@dataclass(slots=True)
class DoubaoResult:
    query: str
    answer_text: str
    answer_lines: List[str]
    raw_text: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlaywrightResponse:
    text: str
    cleaned: str
    streaming: bool = False


class AutomationCancelled(Exception):
    """Raised when upstream requests cancellation of the automation run."""


class DoubaoPlaywrightAutomation:
    """Uses Playwright (connected via CDP or local launch) to automate Doubao."""

    def __init__(self, config: DoubaoMCPConfig) -> None:
        self._config = config
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None
        self._network_hooks_installed = False
        self._cdp_session = None
        self._chunk_listeners: list[Callable[[DoubaoChunk], None]] = []
        self._stream_sequence = 0
        self._last_full_text = ""
        self._should_cancel: Callable[[], bool] = lambda: False

    # ------------------------------------------------------------------
    # context manager helpers
    # ------------------------------------------------------------------
    def __enter__(self) -> "DoubaoPlaywrightAutomation":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401 - context manager cleanup
        self.shutdown()

    def close(self) -> None:
        """Alias for shutdown() to align with common resource patterns."""

        self.shutdown()

    # ------------------------------------------------------------------
    # chunk streaming helpers
    # ------------------------------------------------------------------
    def add_chunk_listener(self, listener: Callable[[DoubaoChunk], None]) -> None:
        """Register a listener to receive incremental chunks."""

        self._chunk_listeners.append(listener)

    def set_cancel_checker(self, checker: Callable[[], bool]) -> None:
        """Install a callable that returns True when the automation should cancel."""

        self._should_cancel = checker

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
        metadata: Optional[dict[str, object]] = None,
    ) -> None:
        if not self._chunk_listeners:
            return
        self._stream_sequence += 1
        chunk = DoubaoChunk(
            delta=delta,
            full_text=full_text,
            source=source,  # type: ignore[arg-type]
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

    def _ensure_page(self) -> None:
        self._check_cancelled()
        if self._page:
            return
        self._pw = sync_playwright().start()
        headless_env = os.getenv("DOUBAO_PLAYWRIGHT_HEADLESS")
        if headless_env is None:
            headless = True
        else:
            headless = headless_env.strip().lower() not in {"0", "false", "no"}

        endpoint = self._config.apply_cdp_override(self._config.cdp_endpoint)
        if endpoint:
            if endpoint != self._config.cdp_endpoint:
                LOGGER.info(
                    "CDP endpoint overridden: {} -> {}",
                    self._config.cdp_endpoint,
                    endpoint,
                )
            self._check_cancelled()
            timeout_ms = max(int(self._config.cdp_connect_timeout * 1000), 1000)
            LOGGER.info(
                "Connecting Playwright over CDP: {} (timeout={}ms)",
                endpoint,
                timeout_ms,
            )
            self._browser = self._pw.chromium.connect_over_cdp(
                endpoint,
                timeout=timeout_ms,
            )
            if self._browser.contexts:
                self._context = self._browser.contexts[0]
            else:
                self._context = self._browser.new_context()
        else:
            LOGGER.info("Launching local Playwright browser (headless={})", headless)
            self._browser = self._pw.chromium.launch(headless=headless, args=self._config.chrome_arguments)
            self._context = self._browser.new_context()
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = self._context.new_page()
        self._install_network_hooks()

    def _navigate(self) -> None:
        assert self._page
        stealth_sync(self._page)
        LOGGER.info("Navigating to Doubao: {}", self._config.base_url)
        self._check_cancelled()
        self._page.goto(self._config.base_url, wait_until="domcontentloaded", timeout=self._config.navigation_timeout * 1000)
        self._page.wait_for_timeout(500)

    def _input_query(self, query: str) -> None:
        assert self._page
        LOGGER.info("Filling query = {}", query)
        locator = self._page.locator(self._config.input_selector)
        self._check_cancelled()
        locator.wait_for(state="visible", timeout=self._config.navigation_timeout * 1000)
        locator.click()
        locator.fill(query)
        send_button_selector = "[data-testid='chat_input_send_button']"
        send_button = self._page.locator(send_button_selector)
        try:
            self._page.wait_for_function(
                "(selector) => {\n                    const btn = document.querySelector(selector);\n                    if (!btn) {\n                        return false;\n                    }\n                    const aria = btn.getAttribute('aria-disabled');\n                    const disabledAttr = btn.getAttribute('disabled');\n                    const pointerEvents = getComputedStyle(btn).pointerEvents;\n                    return aria !== 'true' && disabledAttr !== 'true' && pointerEvents !== 'none';\n                }",
                arg=send_button_selector,
                timeout=5000,
            )
        except PlaywrightTimeoutError:
            LOGGER.warning("Send button remained disabled, fallback to JS trigger")
            self._page.evaluate(
                "(selector) => { const btn = document.querySelector(selector); btn && btn.click(); }",
                send_button_selector,
            )
            return
        self._check_cancelled()
        time.sleep(1.2)
        send_button.click()

    def _wait_for_answer(self) -> PlaywrightResponse:
        timeout_at = time.time() + self._config.response_timeout
        dom_previous_text = ""
        dom_last_cleaned = ""
        dom_stable_runs = 0
        while time.time() < timeout_at:
            self._check_cancelled()
            dom_snapshot = self._read_answer_from_dom()
            if dom_snapshot:
                current_text = dom_snapshot.text or ""
                if current_text and current_text != dom_previous_text:
                    chunks, had_deletion = self._compute_text_diff(dom_previous_text, current_text)
                    dom_previous_text = current_text
                    if chunks:
                        for chunk in chunks:
                            preview = chunk.replace("\n", " ").strip()
                            if len(preview) > 120:
                                preview = f"{preview[:120]}..."
                            LOGGER.debug("DOM chunk += len={} preview={}", len(chunk), preview)
                    elif had_deletion:
                        LOGGER.debug("DOM 文本发生删除或重排，等待后续片段")
                    else:
                        LOGGER.debug("DOM 文本更新但未检测到新增 chunk")
                if dom_snapshot.streaming:
                    dom_stable_runs = 0
                else:
                    if dom_snapshot.cleaned == dom_last_cleaned:
                        dom_stable_runs += 1
                    else:
                        dom_last_cleaned = dom_snapshot.cleaned
                        dom_stable_runs = 0
                    if dom_stable_runs >= 2:
                        LOGGER.info("DOM 回答稳定，返回长度={}", len(dom_snapshot.cleaned))
                        return dom_snapshot
            self._page.wait_for_timeout(self._config.poll_interval * 1000)
        raise TimeoutError("等待豆包 DOM 回应超时")


    def search(self, query: str) -> DoubaoResult:
        self._reset_stream_state()
        self._check_cancelled()
        self._ensure_page()
        self._check_cancelled()
        self._navigate()
        time.sleep(120)
        self._check_cancelled()
        self._input_query(query)
        self._check_cancelled()
        try:
            response = self._wait_for_answer()
        except AutomationCancelled:
            raise
        except Exception as exc:
            self._emit_error(str(exc))
            raise
        self._emit_text_update(response.text, "dom")
        self._last_full_text = response.text
        self._emit_chunk(
            delta="",
            full_text=response.text,
            source="final",
            is_final=True,
            metadata={"base_url": self._config.base_url, "engine": "playwright"},
        )
        answer_lines = [
            line for line in response.text.splitlines()
            if line.strip() and not _is_static_text(_normalize_text(line))
        ]
        if not answer_lines:
            answer_lines = [response.text]
        return DoubaoResult(
            query=query,
            answer_text="\n".join(answer_lines),
            answer_lines=answer_lines,
            raw_text=response.text,
            metadata={"base_url": self._config.base_url, "engine": "playwright"},
        )

    def shutdown(self) -> None:
        """Gracefully close Playwright resources without额外阻塞。"""

        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except PlaywrightError:
            LOGGER.exception("Playwright shutdown failed")
        finally:
            if self._cdp_session:
                try:
                    self._cdp_session.detach()
                except PlaywrightError:
                    LOGGER.debug("CDP 会话关闭失败", exc_info=True)
            self._context = None
            self._browser = None
            self._pw = None
            self._page = None
            self._network_hooks_installed = False
            self._cdp_session = None

    def _install_network_hooks(self) -> None:
        if not self._page or self._network_hooks_installed:
            return
        if not self._context:
            return
        self._network_hooks_installed = True
        # 仅保留 DOM 轮询方案，不额外注入网络监控 Hook。

    def _handle_request(self, request: Request) -> None:
        url = request.url or ""
        if not url.startswith(_COMPLETION_URL_PREFIX):
            return
        post_data = request.post_data or ""
        if isinstance(post_data, str):
            LOGGER.debug("捕获 Doubao completion 请求体，length={}", len(post_data))
        message_id = None
        local_message_id = None
        conversation_id = None
        try:
            payload = json.loads(post_data)
        except (TypeError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict):
            conversation_id = payload.get("conversation_id")
            message_id = payload.get("message_id")
            local_message_id = payload.get("local_message_id")
        LOGGER.info(
            "捕获 Doubao completion 请求: method={} url={} message_id={} local_id={} conversation_id={} body_len={}",
            request.method,
            url,
            message_id or "",
            local_message_id or "",
            conversation_id or "",
            len(post_data) if isinstance(post_data, str) else 0,
        )

    def _handle_response(self, response: Response) -> None:
        url = response.url or ""
        if not url.startswith(_COMPLETION_URL_PREFIX):
            return
        try:
            body_bytes = response.body()
        except PlaywrightError as exc:
            LOGGER.warning("读取 Doubao completion 响应失败: url={} error={}", url, exc)
            return
        body_text = body_bytes.decode("utf-8", errors="ignore")
        preview = body_text.replace("\n", " ")[:200]
        LOGGER.info(
            "捕获 Doubao completion 响应: url={} len={} preview={}{}",
            url,
            len(body_text),
            preview,
            "..." if len(body_text) > 200 else "",
        )

    def _read_answer_from_dom(self) -> Optional[PlaywrightResponse]:
        if not self._page:
            return None
        self._check_cancelled()
        script = """
            (staticTokens) => {
                const trim = (text) => (text || '').replace(/\u200b/g, '').trim();
                const blocks = Array.from(
                    document.querySelectorAll('[data-testid=\"message-block-container\"]')
                );
                for (let i = blocks.length - 1; i >= 0; i -= 1) {
                    const block = blocks[i];
                    if (block.querySelector('[data-testid=\"send_message\"]')) continue;
                    const textNode = block.querySelector('[data-testid=\"message_text_content\"]');
                    const text = trim(textNode ? textNode.innerText : block.innerText);
                    const streaming = (block.getAttribute('data-stream-state') || block.dataset.streamState || '').toLowerCase();
                    if (!text) continue;
                    if (staticTokens.includes(text)) continue;
                    if (/^找到\\s*\\d+\\s*篇资料参考$/.test(text)) continue;
                    return { text, streaming };
                }
                return null;
            }
        """
        try:
            result = self._page.evaluate(script, list(_STATIC_TOKENS))
        except PlaywrightError:
            return None
        self._check_cancelled()
        if not result:
            return None
        text = result.get('text', '')
        cleaned = _normalize_text(text)
        if not cleaned or _is_static_text(cleaned):
            return None
        streaming = str(result.get('streaming', '') or '').lower() in {"loading", "pending", "streaming"}
        full_text = text.strip()
        self._emit_text_update(full_text, "dom")
        return PlaywrightResponse(text=full_text, cleaned=cleaned, streaming=streaming)

    @staticmethod
    def _extract_message_id_from_body(body: str) -> Optional[str]:
        if not body:
            return None
        match = _MESSAGE_ID_RE.search(body)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _compute_text_diff(previous: str, current: str) -> (List[str], bool):
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
