"""Shared data structures for Doubao streaming services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional


StreamSource = Literal["dom", "sse", "final", "error"]


@dataclass(slots=True)
class DoubaoChunk:
    """Incremental chunk emitted during Doubao answer streaming."""

    delta: str
    full_text: str
    source: StreamSource
    sequence: int
    is_final: bool
    timestamp: float
    metadata: Optional[dict[str, Any]] = None
