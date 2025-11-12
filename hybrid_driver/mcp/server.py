"""MCP + FastAPI 服务入口，封装豆包搜索流式能力。"""

from __future__ import annotations

import contextlib
import json
from dataclasses import asdict
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.requests import Request

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context
from mcp.server.session import ServerSession
from mcp.types import CallToolResult, TextContent

from hybrid_driver.log_config import get_logger
from hybrid_driver.mcp.config import ConfigError, DoubaoMCPConfig
from hybrid_driver.services.doubao_stream_service import DoubaoStreamService
from hybrid_driver.services.doubao_types import DoubaoChunk

LOGGER = get_logger(__name__)

try:
    CONFIG = DoubaoMCPConfig.from_env()
except ConfigError as exc:  # noqa: BYB101 - 初始化阶段必须失败
    LOGGER.error("加载 Doubao MCP 配置失败: %s", exc)
    raise

SERVICE = DoubaoStreamService(CONFIG)
MCP_SERVER = FastMCP(
    name="hybrid-driver-doubao",
    streamable_http_path="/",
    instructions="调用 doubao.search 工具以流式获取豆包回答",
)


class SearchRequest(BaseModel):
    """HTTP 搜索请求模型。"""

    searchContent: str = Field(..., description="豆包查询内容")


class SearchResponse(BaseModel):
    """HTTP 搜索响应。"""

    query: str
    answer_text: str
    answer_lines: list[str]
    raw_text: str
    metadata: dict[str, Any]


async def get_service() -> DoubaoStreamService:
    return SERVICE


def _chunk_to_payload(chunk: DoubaoChunk) -> dict[str, Any]:
    payload = asdict(chunk)
    # asdict 会将 Literal 展平为普通 str
    return payload


async def _stream_chunks(
    service: DoubaoStreamService,
    query: str,
) -> AsyncIterator[str]:
    try:
        async for chunk in service.stream_search(query):
            message = json.dumps(_chunk_to_payload(chunk), ensure_ascii=False)
            yield f"{message}\n"
    except TimeoutError as exc:
        LOGGER.warning("流式查询超时: %s", exc)
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - 向上游返回统一异常
        LOGGER.exception("流式查询失败: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@MCP_SERVER.tool(
    name="doubao.search",
    description="在豆包网页输入自然语言问题并返回 AI 回答（支持流式分片）",
)
async def doubao_search(
    searchContent: str,
    ctx: Context[ServerSession, None, Request] | None = None,
) -> CallToolResult:
    if ctx is not None:
        await ctx.info(f"开始处理豆包搜索，请求 id={ctx.request_id}")

    chunks: list[DoubaoChunk] = []
    stream = SERVICE.stream_search(searchContent)
    try:
        async for chunk in stream:
            chunks.append(chunk)
            if ctx is not None:
                payload = json.dumps(_chunk_to_payload(chunk), ensure_ascii=False)
                await ctx.info(payload)
    except TimeoutError as exc:
        if ctx is not None:
            await ctx.error(f"豆包查询超时: {exc}")
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("豆包搜索失败: %s", exc)
        if ctx is not None:
            await ctx.error(f"豆包查询失败: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await stream.aclose()

    if not chunks:
        raise HTTPException(status_code=500, detail="未获取到豆包回答")

    final_text = chunks[-1].full_text
    structured_content = {
        "query": searchContent,
        "chunks": [_chunk_to_payload(chunk) for chunk in chunks],
    }
    if ctx is not None:
        await ctx.info(f"豆包搜索完成，请求 id={ctx.request_id} 分片数={len(chunks)}")
    return CallToolResult(
        content=[TextContent(type="text", text=final_text)],
        structuredContent=structured_content,
    )


@contextlib.asynccontextmanager
async def app_lifespan(_: FastAPI):  # noqa: D401 - FastAPI 生命周期钩子
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(MCP_SERVER.session_manager.run())
        try:
            yield
        finally:
            LOGGER.info("FastAPI 应用停止，准备清理资源")
            try:
                await SERVICE.shutdown()
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("关闭流式服务出现异常: %s", exc)


app = FastAPI(
    title="Hybrid Driver Doubao Streaming Service",
    description="提供豆包搜索的 HTTP 与 MCP 接入能力",
    version="1.0.0",
    lifespan=app_lifespan,
)
app.mount("/mcp", MCP_SERVER.streamable_http_app())


@app.post("/api/search", response_model=SearchResponse)
async def search_endpoint(
    payload: SearchRequest,
    service: DoubaoStreamService = Depends(get_service),
) -> SearchResponse:
    try:
        result = await service.search(payload.searchContent)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("搜索失败: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SearchResponse(
        query=payload.searchContent,
        answer_text=result.answer_text,
        answer_lines=result.answer_lines,
        raw_text=result.raw_text,
        metadata=result.metadata or {},
    )


@app.get("/api/search/stream")
async def search_stream_endpoint(
    query: str,
    service: DoubaoStreamService = Depends(get_service),
) -> StreamingResponse:
    if not query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    generator = _stream_chunks(service, query)
    return StreamingResponse(generator, media_type="application/jsonl")


@app.get("/health", response_class=JSONResponse)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


def run_streamable_http() -> None:
    """保留原 MCP 入口，快速启动 Streamable HTTP 服务。"""

    LOGGER.info("以 streamable-http 模式启动 MCP 服务")
    MCP_SERVER.run(transport="streamable-http")


def main() -> None:
    """兼容历史调用。推荐使用 `uvicorn hybrid_driver.mcp.server:app`."""

    run_streamable_http()


if __name__ == "__main__":
    main()

