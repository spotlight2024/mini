# 豆包搜索流式服务改造方案

## 背景
当前豆包自动化流程分别在 `DoubaoAutomation`（Selenium+CDP）与 `DoubaoPlaywrightAutomation` 中实现。两者都能获取完整回答，但输出为阻塞式字符串：
- `_wait_for_answer` 依赖 DOM 轮询与性能日志（SSE）组合，在确认回答稳定后一次性返回。
- Playwright 版本 `_wait_for_answer` 仅基于 DOM diff，完成后直接返回完整文本。

为了赋能大模型以“边生成边消费”的方式获取搜索结果，需要将片段化数据流式暴露给 MCP 客户端，并同时保留现有一次性输出接口以兼容历史调用场景。

## 当前能力梳理
- **浏览器会话管理**：`DoubaoBusiness` 负责远程 Selenium 会话管理；Playwright 版本在 `_ensure_page` 内自建浏览器实例。
- **回答采集**：
  - DOM 轮询：通过 `message-block-container` 节点读取最新回答，并利用 `_compute_text_diff` 得到增量。
  - SSE 解析：`_drain_event_stream` 读取 `Network.eventSourceMessageReceived`，提取 `event_data` 中的文本并在 `finished` 后返回。
- **同步控制**：两条路径都以 `response_timeout` 控制整体等待时间，并在回答稳定后返回字符串结果。
- **输出形式**：返回 `DoubaoResult`（含 query、answer_text、raw_text 等字段），无流式能力。

局限：
- 只在本地函数内部处理片段，外部无法消费增量。
- Playwright 版本缺少 SSE 回退机制。
- `time.sleep(30)` 等同步阻塞影响关闭体验。
- 日志可能打印敏感请求体，需要规范化。

## 目标能力
1. 提供统一的 `DoubaoStreamService`，对外暴露 `async` 流式接口，可直接 yield DOM/SSE 增量。
2. 在 MCP（Model Context Protocol）工具中，通过 `ctx.stream_text()` 等 API 将增量返回给大模型。
3. 集成 FastAPI，提供 HTTP 和 MCP 双接口，方便调试与多端复用。
4. 支持取消、超时、错误回收，确保资源释放。
5. 遵循日志脱敏策略，并在 README 明确配置。

## 总体架构
```
+--------------------+        +----------------------+        +------------------------+
|  FastAPI App       | <----> |  FastMCP Streamable  | <----> |  DoubaoStreamService   |
|  - /mcp endpoint   |        |  - MCP tools         |        |  - 浏览器/会话管理      |
|  - REST /health    |        |  - ctx.stream_text   |        |  - DOM/SSE 聚合         |
+--------------------+        +----------------------+        +------------------------+
                                                          \---> DoubaoAutomation / Playwright
```
- **服务层 (DoubaoStreamService)**：统一封装现有 Selenium/Playwright 逻辑，负责流式采集、会话复用、取消控制。
- **接口层**：
  - MCP 工具 `doubao.search`：接受 `searchContent`，流式输出，最终返回 `CallToolResult`。
  - REST Endpoints（可选）：`POST /api/search`（阻塞式），`GET /api/search/stream`（SSE）。
- **应用层**：FastAPI 负责挂载 MCP、暴露健康检查、预留鉴权扩展点。
- **执行引擎选择**：通过 `engine` 参数或环境变量 `DOUBAO_DEFAULT_ENGINE` 切换 Playwright/Selenium，二者实现统一接口可互换。

## 模块拆分与职责
- `hybrid_driver/services/doubao_stream_service.py`
  - `DoubaoStreamService`：统一入口，选择调度 Selenium 或 Playwright 实现。
  - `DoubaoStreamSession`：维护单次查询的上下文状态，聚合 DOM/SSE。
  - `DoubaoChunk` 数据类：包含 `delta`, `full_text`, `source`, `timestamp`, `is_final`。
- `hybrid_driver/services/doubao_stream_runner.py`（可选）：对外提供工厂/上下文管理，抽离资源初始化。
- `hybrid_driver/mcp/server.py`
  - 初始化 `FastMCP`，注册工具、资源、提示。
  - 提供 MCP 工具实现，调用服务层，利用 `ctx.stream_text()` 推送。
- `hybrid_driver/api/app.py`
  - FastAPI 应用入口；挂载 `/mcp`、`/health` 等。
  - 提供 REST 接口与服务层对接。
- 文档与配置：
  - 更新 `README.md` 或新增详细文档记录环境变量、日志策略。

## 接口设计
### 1. `DoubaoStreamService`
```python
@dataclass
class DoubaoChunk:
    delta: str
    full_text: str
    source: Literal["dom", "sse"]
    sequence: int
    is_final: bool
    timestamp: float

class DoubaoStreamService:
    async def stream_search(self, query: str, *, session: Optional[str] = None) -> AsyncIterator[DoubaoChunk]:
        ...
```
- `session`：可选会话标识，便于复用浏览器。
- 迭代器在 `is_final=True` 时结束，调用者可自行聚合 `full_text`。
- 内部需处理：
  - DOM diff → delta；
  - SSE → delta；
  - 去重、顺序控制（`sequence` 自增）。
  - 超时、取消（监听 `asyncio.CancelledError`）。

### 2. MCP 工具 `doubao.search`
- 输入 Schema：
```json
{
  "type": "object",
  "properties": {
    "searchContent": {"type": "string"},
    "sessionId": {"type": "string"},
    "engine": {"type": "string", "enum": ["selenium", "playwright"]}
  },
  "required": ["searchContent"]
}
```
- 实现流程：
  1. 解析参数，选择服务实例。
  2. `async for chunk in service.stream_search()`：
     - `await ctx.stream_text(chunk.delta, final=chunk.is_final)`
     - `await ctx.report_progress()` 根据序列长度更新。
  3. 收集最终 `full_text`，返回 `CallToolResult(content=[TextContent(text=full)])`。
  4. 将所有 `chunk` 存入 `structuredContent={"chunks": [...]}` 方便客户端回放。

### 3. REST 接口
- `POST /api/search`
  - 请求：`{"searchContent": "..."}`
  - 响应：`{"text": "...", "chunks": [...]}`
- `GET /api/search/stream`
  - SSE/Chunked 响应，逐段写入 `data: {"delta": "..."}`。
  - 对接 `DoubaoStreamService`，采用 `StreamingResponse`。

## 日志与观测性
- 统一使用 `hybrid_driver.log_config` 获取 logger。
- 关键点：
  - 禁止记录完整 prompt 与 SSE 原始 payload，仅记录长度、阶段、执行耗时。
  - 对错误堆栈使用 `LOGGER.exception`，同时返回结构化错误给调用方。
- FastMCP 中可利用 `ctx.debug/info` 输出面向 MCP 客户端的日志信息。
- 增加基础 metrics：查询总数、平均响应时长、SSE 命中率（可通过自定义路由 `/metrics` 输出）。

## 任务拆分
1. **阶段一（当前）**：梳理方案与接口设计，形成本文档并征求确认。✅
2. **阶段二**：
   - 提取/重构代码形成 `DoubaoStreamService`；
   - 实现 DOM/SSE 聚合、取消、错误处理；
   - 调整现有 `search()` 调用以复用新服务。
3. **阶段三**：
   - 创建 FastAPI + FastMCP 应用结构；
   - 实现 `doubao.search` MCP 工具；
   - 可选 REST 接口与健康检查；
   - 更新 README、添加使用示例。
4. **阶段四（可选）**：
   - 增加自动化测试（集成+回归）；
   - 优化并发调度、支持多会话池；
   - 接入监控/告警。

## 风险与后续优化
- **浏览器资源占用**：流式请求可能导致同时存在多个会话，需要限制并发或实现会话池。
- **SSE 数据格式变动**：豆包接口可能改变 event schema，需保留 DOM 回退与容错解析。
- **网络不稳定**：MCP 流式连接断开需支持重连或合理报错。
- **Playwright/Selenium 差异**：两套实现需复用统一接口，避免行为不一致。
- **安全合规**：日志与 structuredContent 需满足脱敏要求，必要时对文本做关键字过滤。

后续可考虑：
- 引入缓存/索引，减少重复查询。
- 支持多模态回答（图像、引用链接），通过 MCP `resource` 返回。
- 结合 `ctx.session.create_message`，在回答空缺时触发 LLM 后处理。
