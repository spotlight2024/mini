"""
混合驱动（hybrid_driver）在 MCP 场景下的配置工具。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit

from dotenv import dotenv_values


class ConfigError(RuntimeError):
    """环境变量配置异常。"""


_ENV_CACHE: Dict[str, str] | None = None


def _load_env_values() -> Dict[str, str]:
    global _ENV_CACHE
    if _ENV_CACHE is not None:
        return _ENV_CACHE

    project_root = Path(__file__).resolve().parents[2]
    env_file = project_root / ".env"
    values: Dict[str, str] = {}
    if env_file.exists():
        raw_values = dotenv_values(str(env_file))
        values = {key: value for key, value in raw_values.items() if isinstance(key, str) and isinstance(value, str)}
    _ENV_CACHE = values
    return _ENV_CACHE


def _env_get(name: str, default: Optional[str] = None) -> Optional[str]:
    values = _load_env_values()
    if name in values:
        return values[name]
    return default


def _bool_env(name: str, default: bool) -> bool:
    raw = _env_get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _float_env(name: str, default: float) -> float:
    raw = _env_get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:  # noqa: B904
        raise ConfigError(f".env 配置 {name} 必须是浮点数") from exc


def _int_env(name: str, default: Optional[int]) -> Optional[int]:
    raw = _env_get(name)
    if raw is None:
        return default
    if not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:  # noqa: B904
        raise ConfigError(f".env 配置 {name} 必须是整数") from exc


def _list_env(name: str, default: List[str]) -> List[str]:
    raw = _env_get(name)
    if raw is None:
        return default
    parts = [item.strip() for item in raw.split(",")]
    return [item for item in parts if item]


_DEFAULT_REMOTE_URL = "http://172.16.1.129:30444/wd/hub"
_DEFAULT_BASE_URL = "https://www.doubao.com/chat/"
_DEFAULT_INPUT_SELECTOR = "textarea[data-testid=\"chat_input_input\"]"
_DEFAULT_CONTAINER_SELECTOR = "main"
_DEFAULT_SSE_ENDPOINT = "https://www.doubao.com/samantha/chat/completion"
_DEFAULT_CHROME_ARGS = [
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--enable-automation",
]
_DEFAULT_MAX_CONCURRENT_SESSIONS = 2
_DEFAULT_ENGINE = "selenium"
_SUPPORTED_ENGINES = {"playwright", "selenium"}


@dataclass(slots=True)
class DoubaoMCPConfig:
    """豆包 MCP 自动化流程的配置容器。"""

    remote_url: str = _DEFAULT_REMOTE_URL
    base_url: str = _DEFAULT_BASE_URL
    input_selector: str = _DEFAULT_INPUT_SELECTOR
    container_selector: str = _DEFAULT_CONTAINER_SELECTOR
    navigation_timeout: float = 30.0
    response_timeout: float = 45.0
    poll_interval: float = 0.4
    chrome_arguments: List[str] = field(default_factory=lambda: list(_DEFAULT_CHROME_ARGS))
    accept_insecure_certs: bool = False
    reuse_session: bool = True
    remote_capabilities: Dict[str, object] = field(default_factory=dict)
    cdp_endpoint: str | None = "ws://172.16.1.129:30444/session/c11ce592a9567a28557d7361a34ac456/se/cdp"
    cdp_host_override: str | None = None
    cdp_port_override: int | None = None
    cdp_connect_timeout: float = 5.0
    sse_endpoint: str = _DEFAULT_SSE_ENDPOINT
    max_concurrent_sessions: int = _DEFAULT_MAX_CONCURRENT_SESSIONS
    proxy_provider: str | None = None
    default_engine: str = _DEFAULT_ENGINE

    @classmethod
    def from_env(cls) -> "DoubaoMCPConfig":
        remote_url = _env_get("HYBRID_DRIVER_REMOTE_URL", _DEFAULT_REMOTE_URL)
        base_url = _env_get("DOUBAO_BASE_URL", _DEFAULT_BASE_URL)
        input_selector = _env_get("DOUBAO_INPUT_SELECTOR", _DEFAULT_INPUT_SELECTOR)
        container_selector = _env_get("DOUBAO_CONTAINER_SELECTOR", _DEFAULT_CONTAINER_SELECTOR)
        navigation_timeout = _float_env("DOUBAO_NAVIGATION_TIMEOUT", 30.0)
        response_timeout = _float_env("DOUBAO_RESPONSE_TIMEOUT", 45.0)
        poll_interval = _float_env("DOUBAO_POLL_INTERVAL", 0.4)
        chrome_arguments = _list_env("HYBRID_DRIVER_CHROME_ARGS", list(_DEFAULT_CHROME_ARGS))
        accept_insecure_certs = _bool_env("HYBRID_DRIVER_ACCEPT_INSECURE_CERTS", False)
        reuse_session = _bool_env("DOUBAO_REUSE_SESSION", False)
        cdp_endpoint = _env_get("DOUBAO_CDP_ENDPOINT")
        cdp_host_override = _env_get("DOUBAO_CDP_HOST_OVERRIDE")
        cdp_port_override = _int_env("DOUBAO_CDP_PORT_OVERRIDE", None)
        cdp_connect_timeout = _float_env("DOUBAO_CDP_CONNECT_TIMEOUT", 5.0)
        sse_endpoint = _env_get("DOUBAO_SSE_ENDPOINT", _DEFAULT_SSE_ENDPOINT)
        max_concurrent_sessions = _int_env(
            "DOUBAO_MAX_CONCURRENT_SESSIONS",
            _DEFAULT_MAX_CONCURRENT_SESSIONS,
        )
        if max_concurrent_sessions is None:
            max_concurrent_sessions = _DEFAULT_MAX_CONCURRENT_SESSIONS
        if max_concurrent_sessions < 1:
            raise ConfigError("DOUBAO_MAX_CONCURRENT_SESSIONS 必须大于等于 1")

        proxy_provider_raw = _env_get("DOUBAO_PROXY_PROVIDER")
        if proxy_provider_raw:
            proxy_provider = proxy_provider_raw.strip().lower() or None
        else:
            proxy_provider = None

        default_engine_raw = _env_get("DOUBAO_DEFAULT_ENGINE", _DEFAULT_ENGINE)
        default_engine = (default_engine_raw or _DEFAULT_ENGINE).strip().lower()
        if default_engine not in _SUPPORTED_ENGINES:
            raise ConfigError(f"DOUBAO_DEFAULT_ENGINE 必须是 {_SUPPORTED_ENGINES}")

        capabilities_raw = _env_get("HYBRID_DRIVER_REMOTE_CAPABILITIES")
        remote_capabilities: Dict[str, object] = {}
        if capabilities_raw:
            try:
                remote_capabilities = json.loads(capabilities_raw)
            except json.JSONDecodeError as exc:  # noqa: B904
                raise ConfigError("HYBRID_DRIVER_REMOTE_CAPABILITIES 必须是合法 JSON") from exc

        return cls(
            remote_url=remote_url,
            base_url=base_url,
            input_selector=input_selector,
            container_selector=container_selector,
            navigation_timeout=navigation_timeout,
            response_timeout=response_timeout,
            poll_interval=poll_interval,
            chrome_arguments=chrome_arguments,
            accept_insecure_certs=accept_insecure_certs,
            reuse_session=reuse_session,
            remote_capabilities=remote_capabilities,
            cdp_endpoint=cdp_endpoint,
            cdp_host_override=cdp_host_override,
            cdp_port_override=cdp_port_override,
            cdp_connect_timeout=cdp_connect_timeout,
            sse_endpoint=sse_endpoint,
            max_concurrent_sessions=max_concurrent_sessions,
            proxy_provider=proxy_provider,
            default_engine=default_engine,
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "remote_url": self.remote_url,
            "base_url": self.base_url,
            "input_selector": self.input_selector,
            "container_selector": self.container_selector,
            "navigation_timeout": self.navigation_timeout,
            "response_timeout": self.response_timeout,
            "poll_interval": self.poll_interval,
            "chrome_arguments": list(self.chrome_arguments),
            "accept_insecure_certs": self.accept_insecure_certs,
            "reuse_session": self.reuse_session,
            "remote_capabilities": dict(self.remote_capabilities),
            "cdp_endpoint": self.cdp_endpoint,
            "cdp_host_override": self.cdp_host_override,
            "cdp_port_override": self.cdp_port_override,
            "cdp_connect_timeout": self.cdp_connect_timeout,
            "sse_endpoint": self.sse_endpoint,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "proxy_provider": self.proxy_provider,
            "default_engine": self.default_engine,
        }

    def apply_cdp_override(self, endpoint: Optional[str]) -> Optional[str]:
        if not endpoint:
            return endpoint
        host, port = self._resolve_cdp_override_target()
        if not host and port is None:
            return endpoint
        parsed = urlsplit(endpoint)
        final_host = host or parsed.hostname or ""
        final_port = port if port is not None else parsed.port
        if not final_host:
            return endpoint
        netloc = f"{final_host}:{final_port}" if final_port else final_host
        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))

    def _resolve_cdp_override_target(self) -> Tuple[str, Optional[int]]:
        host = (self.cdp_host_override or "").strip()
        port = self.cdp_port_override
        if host and port is not None:
            return host, port

        remote_host, remote_port = self._parse_remote_url()
        if not host:
            host = remote_host or ""
        if port is None:
            port = remote_port
        return host, port

    def _parse_remote_url(self) -> Tuple[Optional[str], Optional[int]]:
        try:
            parsed = urlsplit(self.remote_url)
            return parsed.hostname, parsed.port
        except ValueError:
            return None, None
