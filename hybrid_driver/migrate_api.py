#!/usr/bin/env python3
"""
API迁移脚本 - 帮助从旧API迁移到新的模块化API
"""
import re
import os
import sys
from typing import Dict, List, Tuple


class APIMigrator:
    """API迁移工具类"""
    
    # 旧API到新API的映射
    API_MAPPING = {
        # 设备管理
        r'POST\s+/connect': 'POST /device/connect',
        r'POST\s+/disconnect': 'POST /device/disconnect',
        r'POST\s+/action': 'POST /device/action',
        
        # 元素操作
        r'POST\s+/find_element': 'POST /element/find',
        r'POST\s+/find_elements': 'POST /element/find_all',
        r'POST\s+/click': 'POST /element/click',
        r'POST\s+/run_operations': 'POST /element/operations',
        
        # 页面管理
        r'POST\s+/check_page': 'POST /page/check',
        
        # 数据收集
        r'POST\s+/collect_items': 'POST /collect/items',
        
        # 模拟测试
        r'POST\s+/mock_click': 'POST /mock/click',
        r'POST\s+/mock_find_element': 'POST /mock/find_element',
    }
    
    # URL映射
    URL_MAPPING = {
        '/connect': '/device/connect',
        '/disconnect': '/device/disconnect',
        '/action': '/device/action',
        '/find_element': '/element/find',
        '/find_elements': '/element/find_all',
        '/click': '/element/click',
        '/run_operations': '/element/operations',
        '/check_page': '/page/check',
        '/collect_items': '/collect/items',
        '/mock_click': '/mock/click',
        '/mock_find_element': '/mock/find_element',
    }
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def scan_directory(self, directory: str) -> List[str]:
        """扫描目录中的Python文件"""
        python_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def find_api_calls(self, file_path: str) -> List[Tuple[str, int, str]]:
        """在文件中查找API调用"""
        api_calls = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                for old_pattern, new_pattern in self.API_MAPPING.items():
                    if re.search(old_pattern, line, re.IGNORECASE):
                        api_calls.append((file_path, line_num, line.strip()))
                        break
                
                # 查找URL调用
                for old_url, new_url in self.URL_MAPPING.items():
                    if old_url in line:
                        api_calls.append((file_path, line_num, line.strip()))
                        break
                        
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
        
        return api_calls
    
    def generate_migration_report(self, directory: str) -> str:
        """生成迁移报告"""
        print("扫描目录中的API调用...")
        
        python_files = self.scan_directory(directory)
        all_api_calls = []
        
        for file_path in python_files:
            api_calls = self.find_api_calls(file_path)
            all_api_calls.extend(api_calls)
        
        if not all_api_calls:
            return "未发现需要迁移的API调用"
        
        # 生成报告
        report = []
        report.append("# API迁移报告")
        report.append("")
        report.append(f"扫描目录: {directory}")
        report.append(f"发现文件数: {len(python_files)}")
        report.append(f"需要迁移的API调用数: {len(all_api_calls)}")
        report.append("")
        
        # 按文件分组
        files_dict = {}
        for file_path, line_num, line in all_api_calls:
            if file_path not in files_dict:
                files_dict[file_path] = []
            files_dict[file_path].append((line_num, line))
        
        for file_path, calls in files_dict.items():
            report.append(f"## 文件: {file_path}")
            report.append("")
            
            for line_num, line in calls:
                report.append(f"### 第 {line_num} 行")
                report.append(f"原始代码: `{line}`")
                
                # 提供迁移建议
                migration_suggestion = self.get_migration_suggestion(line)
                if migration_suggestion:
                    report.append(f"建议修改: `{migration_suggestion}`")
                
                report.append("")
        
        # 添加迁移指南
        report.append("## 迁移指南")
        report.append("")
        report.append("### 1. 更新导入语句")
        report.append("```python")
        report.append("# 旧导入")
        report.append("from hybrid_driver.server import app")
        report.append("")
        report.append("# 新导入")
        report.append("from hybrid_driver.server_optimized import app")
        report.append("```")
        report.append("")
        
        report.append("### 2. 更新API端点")
        report.append("| 旧端点 | 新端点 |")
        report.append("|--------|--------|")
        for old_url, new_url in self.URL_MAPPING.items():
            report.append(f"| {old_url} | {new_url} |")
        report.append("")
        
        report.append("### 3. 更新客户端代码")
        report.append("```python")
        report.append("# 旧代码")
        report.append("response = requests.post('http://localhost:8000/connect', json=data)")
        report.append("")
        report.append("# 新代码")
        report.append("response = requests.post('http://localhost:8000/device/connect', json=data)")
        report.append("```")
        
        return "\n".join(report)
    
    def get_migration_suggestion(self, line: str) -> str:
        """获取迁移建议"""
        # 替换URL
        for old_url, new_url in self.URL_MAPPING.items():
            if old_url in line:
                return line.replace(old_url, new_url)
        
        # 替换API模式
        for old_pattern, new_pattern in self.API_MAPPING.items():
            if re.search(old_pattern, line, re.IGNORECASE):
                return re.sub(old_pattern, new_pattern, line, flags=re.IGNORECASE)
        
        return ""
    
    def create_migration_script(self, directory: str, output_file: str = "migrate_api_calls.py"):
        """创建自动迁移脚本"""
        python_files = self.scan_directory(directory)
        all_api_calls = []
        
        for file_path in python_files:
            api_calls = self.find_api_calls(file_path)
            all_api_calls.extend(api_calls)
        
        if not all_api_calls:
            print("未发现需要迁移的API调用")
            return
        
        script_content = [
            "#!/usr/bin/env python3",
            '"""',
            "API调用自动迁移脚本",
            "注意: 请在运行前备份您的代码",
            '"""',
            "import os",
            "import re",
            "import shutil",
            "from pathlib import Path",
            "",
            "# API映射",
            "URL_MAPPING = {",
        ]
        
        for old_url, new_url in self.URL_MAPPING.items():
            script_content.append(f"    '{old_url}': '{new_url}',")
        
        script_content.extend([
            "}",
            "",
            "def migrate_file(file_path):",
            '    """迁移单个文件"""',
            "    try:",
            "        with open(file_path, 'r', encoding='utf-8') as f:",
            "            content = f.read()",
            "",
            "        original_content = content",
            "",
            "        # 替换URL",
            "        for old_url, new_url in URL_MAPPING.items():",
            "            content = content.replace(old_url, new_url)",
            "",
            "        # 如果内容有变化，写回文件",
            "        if content != original_content:",
            "            with open(file_path, 'w', encoding='utf-8') as f:",
            "                f.write(content)",
            "            print(f'已迁移: {file_path}')",
            "            return True",
            "        else:",
            "            print(f'无需迁移: {file_path}')",
            "            return False",
            "    except Exception as e:",
            "        print(f'迁移文件 {file_path} 时出错: {e}')",
            "        return False",
            "",
            "def main():",
            '    """主函数"""',
            f"    directory = '{directory}'",
            "    print(f'开始迁移目录: {directory}')",
            "",
            "    # 创建备份",
            "    backup_dir = f'{directory}_backup'",
            "    if os.path.exists(backup_dir):",
            "        shutil.rmtree(backup_dir)",
            "    shutil.copytree(directory, backup_dir)",
            "    print(f'已创建备份: {backup_dir}')",
            "",
            "    # 迁移所有Python文件",
            "    migrated_count = 0",
            "    for root, dirs, files in os.walk(directory):",
            "        for file in files:",
            "            if file.endswith('.py'):",
            "                file_path = os.path.join(root, file)",
            "                if migrate_file(file_path):",
            "                    migrated_count += 1",
            "",
            "    print(f'迁移完成，共迁移 {migrated_count} 个文件')",
            "    print(f'备份位置: {backup_dir}')",
            "",
            'if __name__ == "__main__":',
            "    main()",
        ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_content))
        
        print(f"已创建迁移脚本: {output_file}")
        print("请在运行前备份您的代码！")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API迁移工具")
    parser.add_argument("directory", help="要扫描的目录")
    parser.add_argument("--report", help="生成迁移报告文件")
    parser.add_argument("--script", help="生成自动迁移脚本")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"目录不存在: {args.directory}")
        sys.exit(1)
    
    migrator = APIMigrator()
    
    if args.report:
        report = migrator.generate_migration_report(args.directory)
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"迁移报告已保存到: {args.report}")
    elif args.script:
        migrator.create_migration_script(args.directory, args.script)
    else:
        # 默认生成报告
        report = migrator.generate_migration_report(args.directory)
        print(report)


if __name__ == "__main__":
    main() 