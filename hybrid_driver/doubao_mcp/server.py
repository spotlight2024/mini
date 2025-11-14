"""MCP + FastAPI 服务入口，封装豆包搜索流式能力。"""

from __future__ import annotations

import contextlib
import json
from dataclasses import asdict
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.requests import Request

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context
from mcp.server.session import ServerSession
from mcp.types import CallToolResult, TextContent

from hybrid_driver.log_config import get_logger
from hybrid_driver.doubao_mcp.config import ConfigError, DoubaoMCPConfig
from hybrid_driver.services.doubao_stream_service import DoubaoStreamService
from hybrid_driver.services.doubao_types import DoubaoChunk

LOGGER = get_logger(__name__)

try:
    CONFIG = DoubaoMCPConfig.from_env()
except ConfigError as exc:  # noqa: BYB101 - 初始化阶段必须失败
    LOGGER.error("加载 Doubao MCP 配置失败: {}", exc)
    raise

SERVICE = DoubaoStreamService(CONFIG)
MCP_SERVER = FastMCP(
    name="hybrid-driver-doubao",
    streamable_http_path="/",
    instructions="调用 doubao.search 工具以流式获取豆包回答",
)
_session_stack: contextlib.AsyncExitStack | None = None
_ROUTER = APIRouter(prefix="/api", tags=["Doubao MCP"])


class SearchRequest(BaseModel):
    """HTTP 搜索请求模型。"""

    searchContent: str = Field(..., description="豆包查询内容")
    engine: str | None = Field(None, description="执行引擎，可选 selenium 或 playwright")


class SearchResponse(BaseModel):
    """HTTP 搜索响应。"""

    query: str
    answer_text: str
    answer_lines: list[str]
    raw_text: str
    metadata: dict[str, Any]
    engine: str


async def get_service() -> DoubaoStreamService:
    return SERVICE


def _chunk_to_payload(chunk: DoubaoChunk) -> dict[str, Any]:
    payload = asdict(chunk)
    # asdict 会将 Literal 展平为普通 str
    return payload


async def _stream_chunks(
    service: DoubaoStreamService,
    query: str,
    engine: str | None,
) -> AsyncIterator[str]:
    try:
        async for chunk in service.stream_search(query, engine=engine):
            message = json.dumps(_chunk_to_payload(chunk), ensure_ascii=False)
            yield f"{message}\n"
    except TimeoutError as exc:
        LOGGER.warning("流式查询超时: {}", exc)
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - 向上游返回统一异常
        LOGGER.exception("流式查询失败: {}", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@MCP_SERVER.tool(
    name="doubao.search",
    description="在豆包网页输入自然语言问题并返回 AI 回答（支持流式分片）",
)
async def doubao_search(
    searchContent: str,
    engine: str | None = None,
    ctx: Context[ServerSession, None, Request] | None = None,
) -> CallToolResult:
    if ctx is not None:
        await ctx.info(f"开始处理豆包搜索，请求 id={ctx.request_id} engine={engine or 'default'}")

    chunks: list[DoubaoChunk] = []
    stream = SERVICE.stream_search(searchContent, engine=engine)

    async def _emit_to_ctx(target_ctx: Context[ServerSession, None, Request], chunk: DoubaoChunk) -> None:
        payload = json.dumps(_chunk_to_payload(chunk), ensure_ascii=False)
        text_piece = chunk.delta or chunk.full_text or ""
        stream_method = getattr(target_ctx, "stream_text", None)
        if callable(stream_method):
            try:
                await stream_method(text_piece, final=chunk.is_final)
            except Exception as exc:  # noqa: BLE001
                LOGGER.debug("ctx.stream_text 调用失败，回退到 info 日志: {}", exc)
                if text_piece:
                    await target_ctx.info(text_piece)
        elif text_piece:
            await target_ctx.info(text_piece)
        await target_ctx.debug(payload)
    try:
        async for chunk in stream:
            chunks.append(chunk)
            if ctx is not None:
                await _emit_to_ctx(ctx, chunk)
    except TimeoutError as exc:
        if ctx is not None:
            await ctx.error(f"豆包查询超时: {exc}")
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("豆包搜索失败: {}", exc)
        if ctx is not None:
            await ctx.error(f"豆包查询失败: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await stream.aclose()

    if not chunks:
        raise HTTPException(status_code=500, detail="未获取到豆包回答")

    final_text = chunks[-1].full_text
    final_engine = (chunks[-1].metadata or {}).get("engine", SERVICE.default_engine)
    structured_content = {
        "query": searchContent,
        "engine": final_engine,
        "chunks": [_chunk_to_payload(chunk) for chunk in chunks],
    }
    if ctx is not None:
        await ctx.info(f"豆包搜索完成，请求 id={ctx.request_id} 分片数={len(chunks)}")
    return CallToolResult(
        content=[TextContent(type="text", text=final_text)],
        structuredContent=structured_content,
    )


async def _startup_event() -> None:
    """初始化 MCP Session，供 HTTP/SSE 复用。"""
    global _session_stack  # noqa: PLW0603 - 生命周期需要保存全局状态
    stack = contextlib.AsyncExitStack()
    await stack.enter_async_context(MCP_SERVER.session_manager.run())
    _session_stack = stack


async def _shutdown_event() -> None:
    """释放 MCP 相关资源。"""
    global _session_stack  # noqa: PLW0603
    stack = _session_stack
    _session_stack = None
    if stack is not None:
        await stack.aclose()
    try:
        await SERVICE.shutdown()
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("关闭流式服务出现异常: {}", exc)


def register_events(app: FastAPI) -> None:
    """向指定 FastAPI 实例注册启动/关闭事件。"""
    flag = "_doubao_mcp_events_registered"
    if getattr(app.state, flag, False):
        return
    app.add_event_handler("startup", _startup_event)
    app.add_event_handler("shutdown", _shutdown_event)
    setattr(app.state, flag, True)


def register_routes(app: FastAPI, *, prefix: str | None = None) -> None:
    """将豆包相关 HTTP 路由挂载到目标应用。"""
    include_kwargs: dict[str, Any] = {}
    if prefix is not None:
        include_kwargs["prefix"] = prefix
    app.include_router(_ROUTER, **include_kwargs)


def mount_transport(app: FastAPI, path: str = "/mcp") -> None:
    """挂载 MCP Streamable HTTP 子应用到指定路径。"""
    attr_name = "_doubao_mcp_transport_paths"
    mounted_paths: set[str] = getattr(app.state, attr_name, set())
    if path in mounted_paths:
        return
    app.mount(path, MCP_SERVER.streamable_http_app())
    mounted_paths.add(path)
    setattr(app.state, attr_name, mounted_paths)


@_ROUTER.post("/search", response_model=SearchResponse)
async def search_endpoint(
    payload: SearchRequest,
    service: DoubaoStreamService = Depends(get_service),
) -> SearchResponse:
    try:
        result = await service.search(payload.searchContent, engine=payload.engine)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("搜索失败: {}", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SearchResponse(
        query=payload.searchContent,
        answer_text=result.answer_text,
        answer_lines=result.answer_lines,
        raw_text=result.raw_text,
        metadata=result.metadata or {},
        engine=(result.metadata or {}).get("engine", service.default_engine),
    )


@_ROUTER.get("/search/stream")
async def search_stream_endpoint(
    query: str,
    engine: str | None = None,
    service: DoubaoStreamService = Depends(get_service),
) -> StreamingResponse:
    if not query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    generator = _stream_chunks(service, query, engine)
    return StreamingResponse(generator, media_type="application/jsonl")


def create_app(
    *,
    http_prefix: str | None = None,
    transport_path: str = "/mcp",
    fastapi_kwargs: dict[str, Any] | None = None,
) -> FastAPI:
    """创建独立运行的豆包 MCP FastAPI 应用。"""
    kwargs: dict[str, Any] = {
        "title": "Hybrid Driver Doubao Streaming Service",
        "description": "提供豆包搜索的 HTTP 与 MCP 接入能力",
        "version": "1.0.0",
    }
    if fastapi_kwargs:
        kwargs.update(fastapi_kwargs)

    app = FastAPI(**kwargs)
    register_events(app)
    register_routes(app, prefix=http_prefix)
    mount_transport(app, path=transport_path)

    @app.get("/health", response_class=JSONResponse)
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {
            "message": "SpotLight Hybrid Driver Doubao MCP Service",
            "version": kwargs["version"],
            "docs": "/docs",
            "mcp_transport": transport_path,
        }

    return app


app = create_app()


def run_streamable_http() -> None:
    """保留原 MCP 入口，快速启动 Streamable HTTP 服务。"""

    LOGGER.info("以 streamable-http 模式启动 MCP 服务")
    MCP_SERVER.run(transport="streamable-http")


def main() -> None:
    """兼容历史调用。推荐使用 `uvicorn hybrid_driver.doubao_mcp.server:app`."""

    run_streamable_http()


if __name__ == "__main__":
    main()

