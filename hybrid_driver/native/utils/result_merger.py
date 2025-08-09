"""结果合并工具"""

import json
from typing import List, Any, Dict
from ..models.script_models import CommandResult


class ResultMerger:
    """结果合并工具类"""

    @staticmethod
    def merge_results(results: List[CommandResult]) -> CommandResult:
        """
        合并多个命令执行结果

        Args:
            results: 命令结果列表

        Returns:
            CommandResult: 合并后的结果
        """
        if not results:
            return CommandResult(code=1, message="No results to merge")

        # 如果只有一个结果，直接返回该结果
        if len(results) == 1:
            return results[0]

        # 检查是否有失败的结果
        failed_results = [result for result in results if result.is_failure()]
        if failed_results:
            # 返回第一个失败的结果
            return failed_results[0]

        # 所有结果都成功，合并数据
        return ResultMerger._merge_successful_results(results)

    @staticmethod
    def _merge_successful_results(results: List[CommandResult]) -> CommandResult:
        """
        合并成功的结果

        Args:
            results: 成功的结果列表

        Returns:
            CommandResult: 合并后的结果
        """
        merged_data: Dict[str, Any] = {}

        for i, result in enumerate(results):
            if result.data:
                try:
                    # 尝试解析 JSON 数据
                    if isinstance(result.data, str):
                        item_data = json.loads(result.data)
                    else:
                        item_data = result.data

                    # 合并 JSON 对象
                    if isinstance(item_data, dict):
                        merged_data.update(item_data)
                    else:
                        # 如果不是字典，使用索引作为键
                        merged_data[f"result_{i}"] = item_data

                except (json.JSONDecodeError, TypeError) as e:
                    print(f"[WARNING] Failed to merge result data at index {i}: {e}")
                    # 如果解析失败，直接使用原始数据
                    merged_data[f"result_{i}"] = result.data

        return CommandResult(
            code=0,
            data=json.dumps(merged_data, ensure_ascii=False) if merged_data else None,
            message="success"
        )

    @staticmethod
    def get_summary(results: List[CommandResult]) -> Dict[str, Any]:
        """
        获取结果摘要信息

        Args:
            results: 结果列表

        Returns:
            Dict[str, Any]: 摘要信息
        """
        if not results:
            return {
                "total": 0,
                "success": 0,
                "failure": 0,
                "success_rate": 0.0
            }

        total = len(results)
        success_count = sum(1 for result in results if result.is_success())
        failure_count = total - success_count
        success_rate = success_count / total if total > 0 else 0.0

        return {
            "total": total,
            "success": success_count,
            "failure": failure_count,
            "success_rate": success_rate,
            "has_failure": failure_count > 0
        }

    @staticmethod
    def extract_data_values(results: List[CommandResult]) -> List[Any]:
        """
        提取所有结果的数据值

        Args:
            results: 结果列表

        Returns:
            List[Any]: 数据值列表
        """
        data_values = []

        for result in results:
            if result.data:
                try:
                    if isinstance(result.data, str):
                        parsed_data = json.loads(result.data)
                        data_values.append(parsed_data)
                    else:
                        data_values.append(result.data)
                except (json.JSONDecodeError, TypeError):
                    # 如果解析失败，使用原始字符串
                    data_values.append(result.data)

        return data_values

    @staticmethod
    def get_error_messages(results: List[CommandResult]) -> List[str]:
        """
        获取所有错误消息

        Args:
            results: 结果列表

        Returns:
            List[str]: 错误消息列表
        """
        error_messages = []

        for result in results:
            if result.is_failure() and result.message:
                error_messages.append(result.message)

        return error_messages

    @staticmethod
    def create_aggregated_result(results: List[CommandResult], include_summary: bool = True) -> CommandResult:
        """
        创建聚合结果，包含详细信息和摘要

        Args:
            results: 结果列表
            include_summary: 是否包含摘要信息

        Returns:
            CommandResult: 聚合结果
        """
        if not results:
            return CommandResult(code=1, message="No results to aggregate")

        summary = ResultMerger.get_summary(results)

        # 如果有失败的结果，返回失败状态
        if summary["has_failure"]:
            first_failure = next(result for result in results if result.is_failure())

            if include_summary:
                aggregated_data = {
                    "summary": summary,
                    "error": first_failure.message,
                    "failed_result": {
                        "code": first_failure.code,
                        "data": first_failure.data,
                        "message": first_failure.message
                    }
                }
                return CommandResult(
                    code=first_failure.code,
                    data=json.dumps(aggregated_data, ensure_ascii=False),
                    message=first_failure.message
                )
            else:
                return first_failure

        # 所有结果都成功
        merged_result = ResultMerger._merge_successful_results(results)

        if include_summary:
            try:
                merged_data = json.loads(merged_result.data) if merged_result.data else {}
                aggregated_data = {
                    "summary": summary,
                    "data": merged_data
                }
                merged_result.data = json.dumps(aggregated_data, ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                # 如果解析失败，保持原始数据
                pass

        return merged_result