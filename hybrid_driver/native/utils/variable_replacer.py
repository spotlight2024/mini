"""变量替换工具"""

import re
from typing import Dict, Optional
from ..services.encoding_service import EncodingService
from ..exceptions.executor_exceptions import VariableReplacementException


class VariableReplacer:
    """变量替换工具类"""

    # 变量占位符的正则表达式模式
    VARIABLE_PATTERN = r'\{\{([^}]+)\}\}'

    def __init__(self, params: Optional[Dict[str, str]] = None, encoding_service: Optional[EncodingService] = None):
        """
        初始化变量替换器

        Args:
            params: 参数字典
            encoding_service: 编码服务实例
        """
        self.params = params or {}
        self.encoding_service = encoding_service or EncodingService()
        self.variables: Dict[str, str] = {}
        self.pattern = re.compile(r'\{\{([^}]+)\}\}')

    def replace_variables(self, commands: str) -> str:
        """
        替换commands中的变量占位符

        Args:
            commands: 包含{{PARAM_NAME}}格式占位符的命令字符串

        Returns:
            str: 替换变量后的命令字符串

        Raises:
            VariableReplacementException: 当变量替换失败时
        """
        if not commands:
            return commands

        try:
            def replace_variable(match):
                param_name = match.group(1).strip()  # 获取{{}}中的参数名并去除空格

                if param_name in self.params:
                    # 获取参数值并进行编码
                    param_value = self.params[param_name]
                    encoded_value = self.encoding_service.encode_string(param_value)
                    print(f"[VARIABLE_REPLACE] {param_name} = '{param_value}' -> '{encoded_value}'")
                    return encoded_value
                else:
                    print(f"[VARIABLE_REPLACE] Warning: Parameter '{param_name}' not found in params")
                    return match.group(0)  # 如果找不到参数，保持原样

            # 使用正则表达式查找并替换所有{{PARAM_NAME}}格式的占位符
            result = re.sub(self.VARIABLE_PATTERN, replace_variable, commands)

            if result != commands:
                print(f"[VARIABLE_REPLACE] Original: {commands}")
                print(f"[VARIABLE_REPLACE] Replaced: {result}")

            return result

        except Exception as e:
            raise VariableReplacementException(f"Failed to replace variables in commands: {e}") from e

    def add_param(self, name: str, value: str) -> None:
        """
        添加参数

        Args:
            name: 参数名
            value: 参数值
        """
        self.params[name] = value

    def remove_param(self, name: str) -> None:
        """
        移除参数

        Args:
            name: 参数名
        """
        self.params.pop(name, None)

    def get_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取参数值

        Args:
            name: 参数名
            default: 默认值

        Returns:
            Optional[str]: 参数值或默认值
        """
        return self.params.get(name, default)

    def has_param(self, name: str) -> bool:
        """
        检查是否存在指定参数

        Args:
            name: 参数名

        Returns:
            bool: 存在返回True
        """
        return name in self.params

    def get_all_params(self) -> Dict[str, str]:
        """
        获取所有参数的副本

        Returns:
            Dict[str, str]: 参数字典的副本
        """
        return self.params.copy()

    def clear_params(self) -> None:
        """清空所有参数"""
        self.params.clear()

    def find_variables(self, commands: str) -> list[str]:
        """
        查找命令中的所有变量名

        Args:
            commands: 命令字符串

        Returns:
            list[str]: 变量名列表
        """
        if not commands:
            return []

        matches = re.findall(self.VARIABLE_PATTERN, commands)
        return [match.strip() for match in matches]

    def validate_variables(self, commands: str) -> tuple[bool, list[str]]:
        """
        验证命令中的所有变量是否都有对应的参数

        Args:
            commands: 命令字符串

        Returns:
            tuple[bool, list[str]]: (是否全部有效, 缺失的变量名列表)
        """
        variables = self.find_variables(commands)
        missing_vars = [var for var in variables if var not in self.params]
        return len(missing_vars) == 0, missing_vars