# ADB Proxy 组件说明

## 一、项目原理

本组件实现了一个基于 `asyncio` 的异步 ADB 代理服务，监听本地 5037 端口，将所有 ADB 客户端请求转发到后端真实 ADB 服务（如 127.0.0.1:5038），并在转发过程中支持请求和响应的 hook（可用于 mock、日志、协议分析等）。

核心原理：
- 采用异步 IO，支持高并发多客户端连接。
- 每个连接独立维护，互不干扰。
- 支持在请求/响应流中插入自定义处理逻辑（如命令 mock、内容替换等）。
- 典型用例：拦截并替换 `grep -a '@webview_devtools_remote_.*' /proc/net/unix` 命令中的 pid，实现 WebView 调试端口的 mock。

## 二、主要代码结构

- `adb_proxy.py`：主程序，包含代理服务、连接管理、hook 机制、日志等。
  - `ProxyConnection`：每个客户端连接的上下文，负责数据转发和生命周期管理。
  - `request_hook`/`response_hook`：请求/响应流的 hook，可自定义处理逻辑。
  - `replace_webview_devtools_pid`：用于精准替换特定命令中的 pid。
  - `log_data`：详细记录每次数据流动内容。
- `proxy.log`：运行时日志文件。
- `__init__.py`：包初始化文件。

## 三、使用方式

### 1. 启动代理

```bash
python3 adb_proxy.py
```
默认监听 0.0.0.0:5037，转发到 127.0.0.1:5038。

### 2. 自定义请求 hook

在 `request_hook` 中调用 `replace_webview_devtools_pid`，并传入你想 mock 的 pid：

```python
async def request_hook(data: bytes, peername=None) -> bytes:
    new_pid = "12345"  # 你的目标 pid
    return replace_webview_devtools_pid(data, new_pid)
```

如需根据不同 client 分配不同 pid，可在 `ProxyConnection` 中维护 pid 属性。

### 3. 典型 mock 场景

- 只拦截并替换 `grep -a '@webview_devtools_remote_.*' /proc/net/unix` 这类命令，其他请求不做处理。
- 支持多 client 并发连接，互不影响。

## 四、日志说明

- 日志文件为 `proxy.log`，记录所有连接、请求、响应、hook 处理等详细信息。
- 日志格式包含时间、级别、内容、peername、HEX/STR 数据等。

## 五、注意事项

- **多 client 并发**：每个连接独立，hook 逻辑不会串号，但需确保 pid 分配正确。
- **性能**：异步模型高效，日志量大时建议优化日志级别或异步写入。
- **扩展性**：如需支持更多 mock 场景，建议将 hook 逻辑做成可配置/插件化。
- **安全性**：仅对特定命令做 mock，避免误处理其他请求。

## 六、常见问题

- 如何区分不同 client？
  - 可通过 `peername` (IP, 端口) 区分。
- 如何只 mock 某个 client？
  - 在 hook 里判断 peername。
- 如何支持多 pid？
  - 在 `ProxyConnection` 里为每个连接分配独立 pid。

---
如需更复杂的 mock 或扩展，建议参考源码注释并根据实际需求调整。 