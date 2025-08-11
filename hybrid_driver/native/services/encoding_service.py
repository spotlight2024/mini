"""编码服务"""

from typing import Set, Optional


class EncodingService:
    """编码服务类，用于处理字符串的十六进制编码和解码"""

    def __init__(self):
        from ..config import Config
        # 从配置文件获取特殊字符集合
        self.HEX_CHARS = Config.ENCODING_SPECIAL_CHARS

    def encode_string(self, text: Optional[str]) -> str:
        """
        将字符串中的特殊字符进行十六进制编码

        Args:
            text: 需要编码的字符串

        Returns:
            str: 编码后的字符串
        """
        if not text:
            return text or ""

        result = []
        for char in text:
            if char in self.HEX_CHARS:
                # 将特殊字符转换为 %XX 格式
                result.append(f'%{ord(char):02X}')
            else:
                result.append(char)

        return ''.join(result)

    def decode_string(self, encoded_text: Optional[str]) -> str:
        """
        将十六进制编码的字符串解码回原始字符串

        Args:
            encoded_text: 编码后的字符串

        Returns:
            str: 解码后的字符串
        """
        if not encoded_text:
            return encoded_text or ""

        result = []
        i = 0
        while i < len(encoded_text):
            if encoded_text[i] == '%' and i + 2 < len(encoded_text):
                try:
                    # 尝试解析十六进制编码
                    hex_code = encoded_text[i + 1:i + 3]
                    char_code = int(hex_code, 16)
                    result.append(chr(char_code))
                    i += 3
                except ValueError:
                    # 如果解析失败，保持原字符
                    result.append(encoded_text[i])
                    i += 1
            else:
                result.append(encoded_text[i])
                i += 1

        return ''.join(result)

    def add_special_char(self, char: str) -> None:
        """
        添加需要编码的特殊字符

        Args:
            char: 要添加的特殊字符
        """
        if len(char) == 1:
            self.HEX_CHARS.add(char)

    def remove_special_char(self, char: str) -> None:
        """
        移除特殊字符

        Args:
            char: 要移除的特殊字符
        """
        self.HEX_CHARS.discard(char)

    def get_special_chars(self) -> Set[str]:
        """
        获取当前的特殊字符集合

        Returns:
            Set[str]: 特殊字符集合的副本
        """
        return self.HEX_CHARS.copy()

    def is_special_char(self, char: str) -> bool:
        """
        检查字符是否为特殊字符

        Args:
            char: 要检查的字符

        Returns:
            bool: 如果是特殊字符返回True
        """
        return char in self.HEX_CHARS