"""
基于 Selenium RemoteWebDriver 的 CDP 调用封装。
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from selenium.webdriver.remote.webdriver import WebDriver


class CDPExecutionError(RuntimeError):
    """CDP 指令执行失败。"""


class SeleniumCDPClient:
    """为常用 CDP 调用提供简单包装。"""

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver

    def evaluate(
        self,
        expression: str,
        *,
        await_promise: bool = True,
        return_by_value: bool = True,
    ) -> Any:
        params: Dict[str, Any] = {
            "expression": expression,
            "includeCommandLineAPI": True,
        }
        if await_promise:
            params["awaitPromise"] = True
        if return_by_value:
            params["returnByValue"] = True
        try:
            result = self._driver.execute_cdp_cmd("Runtime.evaluate", params)
        except Exception as exc:  # noqa: BLE001
            raise CDPExecutionError(f"Runtime.evaluate 执行失败: {expression[:60]}...") from exc

        if "exceptionDetails" in result:
            raise CDPExecutionError(json.dumps(result["exceptionDetails"], ensure_ascii=False))
        value = result.get("result", {})
        if return_by_value and isinstance(value, dict) and "value" in value:
            return value["value"]
        return value

    def call_function(
        self,
        function_body: str,
        *,
        object_id: Optional[str] = None,
        arguments: Optional[list[Dict[str, Any]]] = None,
        await_promise: bool = True,
        return_by_value: bool = True,
    ) -> Any:
        params: Dict[str, Any] = {
            "functionDeclaration": function_body,
        }
        if object_id:
            params["objectId"] = object_id
        if arguments:
            params["arguments"] = arguments
        if await_promise:
            params["awaitPromise"] = True
        if return_by_value:
            params["returnByValue"] = True
        try:
            result = self._driver.execute_cdp_cmd("Runtime.callFunctionOn", params)
        except Exception as exc:  # noqa: BLE001
            raise CDPExecutionError(f"Runtime.callFunctionOn 执行失败: {function_body[:60]}...") from exc

        if "exceptionDetails" in result:
            raise CDPExecutionError(json.dumps(result["exceptionDetails"], ensure_ascii=False))
        value = result.get("result", {})
        if return_by_value and isinstance(value, dict) and "value" in value:
            return value["value"]
        return value

