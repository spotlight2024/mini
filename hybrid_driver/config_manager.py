#!/usr/bin/env python3
"""
配置管理工具
用于管理、验证、导出配置
"""
import os
import json
import argparse
from pathlib import Path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hybrid_driver.config.settings import Settings


class ConfigManager:
    """配置管理工具类"""
    
    def __init__(self):
        self.settings = Settings()
    
    def print_current_config(self):
        """打印当前配置"""
        print("=" * 60)
        print("当前配置信息")
        print("=" * 60)
        self.settings.print_config()
    
    def export_config(self, output_file: str = None):
        """导出配置到文件"""
        if output_file is None:
            output_file = "config_export.json"
        
        try:
            config_data = self.settings.get_config()
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            print(f"配置已导出到: {output_file}")
        except Exception as e:
            print(f"导出配置失败: {e}")
    
    def import_config(self, config_file: str):
        """从文件导入配置"""
        try:
            self.settings.load_from_file(config_file)
            print(f"配置已从文件导入: {config_file}")
        except Exception as e:
            print(f"导入配置失败: {e}")
    
    def validate_config(self):
        """验证配置"""
        print("验证配置...")
        if self.settings.validate_config():
            print("✅ 配置验证通过")
            return True
        else:
            print("❌ 配置验证失败")
            return False
    
    def create_env_file(self, output_file: str = ".env"):
        """创建环境变量文件"""
        try:
            env_content = []
            env_content.append("# SpotLight Hybrid Driver 环境变量配置")
            env_content.append("# 复制此文件为 .env 并根据需要修改")
            env_content.append("")
            
            # API配置
            env_content.append("# ==================== API服务配置 ====================")
            env_content.append(f"API_HOST={self.settings.API_HOST}")
            env_content.append(f"API_PORT={self.settings.API_PORT}")
            env_content.append(f"API_RELOAD={str(self.settings.API_RELOAD).lower()}")
            env_content.append(f"API_WORKERS={self.settings.API_WORKERS}")
            env_content.append(f"API_TITLE={self.settings.API_TITLE}")
            env_content.append(f"API_DESCRIPTION={self.settings.API_DESCRIPTION}")
            env_content.append(f"API_VERSION={self.settings.API_VERSION}")
            env_content.append("")
            
            # 日志配置
            env_content.append("# ==================== 日志配置 ====================")
            env_content.append(f"LOG_LEVEL={self.settings.LOG_LEVEL}")
            env_content.append(f"LOG_FORMAT={self.settings.LOG_FORMAT}")
            env_content.append(f"LOG_FILE={self.settings.LOG_FILE}")
            env_content.append(f"LOG_MAX_SIZE={self.settings.LOG_MAX_SIZE}")
            env_content.append(f"LOG_BACKUP_COUNT={self.settings.LOG_BACKUP_COUNT}")
            env_content.append(f"LOG_ENABLE_CONSOLE={str(self.settings.LOG_ENABLE_CONSOLE).lower()}")
            env_content.append(f"LOG_ENABLE_FILE={str(self.settings.LOG_ENABLE_FILE).lower()}")
            env_content.append("")
            
            # WebDriver配置
            env_content.append("# ==================== WebDriver配置 ====================")
            env_content.append(f"SELENIUM_TIMEOUT={self.settings.SELENIUM_TIMEOUT}")
            env_content.append(f"APPIUM_TIMEOUT={self.settings.APPIUM_TIMEOUT}")
            env_content.append(f"CHROME_DRIVER_PATH={self.settings.CHROME_DRIVER_PATH or ''}")
            env_content.append(f"CHROME_DRIVER_VERSION={self.settings.CHROME_DRIVER_VERSION or ''}")
            env_content.append(f"CHROME_DRIVER_DOWNLOAD_URL={self.settings.CHROME_DRIVER_DOWNLOAD_URL or ''}")
            env_content.append(f"APPIUM_SERVER_URL={self.settings.APPIUM_SERVER_URL}")
            env_content.append(f"WEBDRIVER_MODE={self.settings.WEBDRIVER_MODE}")
            env_content.append(f"REMOTE_WEBDRIVER_URL={self.settings.REMOTE_WEBDRIVER_URL or ''}")
            env_content.append("")
            
            # Selenium Grid配置
            env_content.append("# Selenium Grid配置")
            env_content.append(f"SELENIUM_HUB_HOST={self.settings.SELENIUM_HUB_HOST}")
            env_content.append(f"SELENIUM_HUB_PUBLISH_PORT={self.settings.SELENIUM_HUB_PUBLISH_PORT}")
            env_content.append(f"SELENIUM_HUB_SUBSCRIBE_PORT={self.settings.SELENIUM_HUB_SUBSCRIBE_PORT}")
            env_content.append(f"SELENIUM_NODE_COUNT={self.settings.SELENIUM_NODE_COUNT}")
            env_content.append(f"SELENIUM_NODE_MAX_SESSIONS={self.settings.SELENIUM_NODE_MAX_SESSIONS}")
            env_content.append(f"SELENIUM_NODE_SESSION_TIMEOUT={self.settings.SELENIUM_NODE_SESSION_TIMEOUT}")
            env_content.append("")
            
            # 设备池配置
            env_content.append("# ==================== 设备池配置 ====================")
            env_content.append(f"MAX_DEVICES={self.settings.MAX_DEVICES}")
            env_content.append(f"CLEANUP_INTERVAL={self.settings.CLEANUP_INTERVAL}")
            env_content.append(f"DEVICE_TIMEOUT={self.settings.DEVICE_TIMEOUT}")
            env_content.append(f"DEVICE_CONNECTION_RETRY={self.settings.DEVICE_CONNECTION_RETRY}")
            env_content.append(f"DEVICE_CONNECTION_RETRY_DELAY={self.settings.DEVICE_CONNECTION_RETRY_DELAY}")
            env_content.append("")
            
            # 操作配置
            env_content.append("# ==================== 操作配置 ====================")
            env_content.append(f"DEFAULT_TIMEOUT={self.settings.DEFAULT_TIMEOUT}")
            env_content.append(f"DEFAULT_WAIT={self.settings.DEFAULT_WAIT}")
            env_content.append(f"ELEMENT_WAIT_TIMEOUT={self.settings.ELEMENT_WAIT_TIMEOUT}")
            env_content.append(f"PAGE_LOAD_TIMEOUT={self.settings.PAGE_LOAD_TIMEOUT}")
            env_content.append(f"SCRIPT_TIMEOUT={self.settings.SCRIPT_TIMEOUT}")
            env_content.append("")
            
            # 线程池配置
            env_content.append("# ==================== 线程池配置 ====================")
            env_content.append(f"THREAD_POOL_MAX_WORKERS={self.settings.THREAD_POOL_MAX_WORKERS}")
            env_content.append(f"THREAD_POOL_MIN_WORKERS={self.settings.THREAD_POOL_MIN_WORKERS}")
            env_content.append("")
            
            # 连接池配置
            env_content.append("# ==================== 连接池配置 ====================")
            env_content.append(f"CONNECTION_POOL_MAX_CONNECTIONS={self.settings.CONNECTION_POOL_MAX_CONNECTIONS}")
            env_content.append(f"CONNECTION_POOL_MAX_IDLE_TIME={self.settings.CONNECTION_POOL_MAX_IDLE_TIME}")
            env_content.append("")
            
            # 网络配置
            env_content.append("# ==================== 网络配置 ====================")
            env_content.append(f"NETWORK_NAME={self.settings.NETWORK_NAME}")
            env_content.append(f"NETWORK_TIMEOUT={self.settings.NETWORK_TIMEOUT}")
            env_content.append("")
            
            # 证书配置
            env_content.append("# ==================== 证书配置 ====================")
            env_content.append(f"SE_INSTALL_CERTIFICATES={str(self.settings.SE_INSTALL_CERTIFICATES).lower()}")
            env_content.append("")
            
            # 缓存配置
            env_content.append("# ==================== 缓存配置 ====================")
            env_content.append(f"CACHE_ENABLED={str(self.settings.CACHE_ENABLED).lower()}")
            env_content.append(f"CACHE_TTL={self.settings.CACHE_TTL}")
            env_content.append(f"CACHE_MAX_SIZE={self.settings.CACHE_MAX_SIZE}")
            env_content.append("")
            
            # 监控配置
            env_content.append("# ==================== 监控配置 ====================")
            env_content.append(f"METRICS_ENABLED={str(self.settings.METRICS_ENABLED).lower()}")
            env_content.append(f"METRICS_INTERVAL={self.settings.METRICS_INTERVAL}")
            env_content.append(f"AUTO_SCALE_ENABLED={str(self.settings.AUTO_SCALE_ENABLED).lower()}")
            env_content.append("")
            
            # 安全配置
            env_content.append("# ==================== 安全配置 ====================")
            env_content.append(f"CORS_ENABLED={str(self.settings.CORS_ENABLED).lower()}")
            env_content.append(f"CORS_ORIGINS={','.join(self.settings.CORS_ORIGINS)}")
            env_content.append(f"API_KEY_ENABLED={str(self.settings.API_KEY_ENABLED).lower()}")
            env_content.append(f"API_KEY_HEADER={self.settings.API_KEY_HEADER}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_content))
            
            print(f"环境变量文件已创建: {output_file}")
            print("请复制此文件为 .env 并根据需要修改配置")
            
        except Exception as e:
            print(f"创建环境变量文件失败: {e}")
    
    def create_config_template(self, output_file: str = "config/config.json"):
        """创建配置模板文件"""
        try:
            config_data = self.settings.get_config()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"配置模板已创建: {output_file}")
            
        except Exception as e:
            print(f"创建配置模板失败: {e}")
    
    def show_config_sources(self):
        """显示配置来源"""
        print("=" * 60)
        print("配置来源信息")
        print("=" * 60)
        
        # 检查环境变量文件
        env_files = [".env", ".env.local", ".env.production"]
        for env_file in env_files:
            if os.path.exists(env_file):
                print(f"✅ 环境变量文件: {env_file}")
            else:
                print(f"❌ 环境变量文件: {env_file} (不存在)")
        
        # 检查配置文件
        config_file = os.path.join(self.settings.CONFIG_DIR, "config.json")
        if os.path.exists(config_file):
            print(f"✅ 配置文件: {config_file}")
        else:
            print(f"❌ 配置文件: {config_file} (不存在)")
        
        print(f"\n当前使用的配置:")
        print(f"  - API端口: {self.settings.API_PORT}")
        print(f"  - 日志级别: {self.settings.LOG_LEVEL}")
        print(f"  - WebDriver模式: {self.settings.WEBDRIVER_MODE}")
        print(f"  - 线程池大小: {self.settings.THREAD_POOL_MAX_WORKERS}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SpotLight 配置管理工具")
    parser.add_argument("action", choices=[
        "show", "export", "import", "validate", 
        "create-env", "create-template", "sources"
    ], help="要执行的操作")
    parser.add_argument("--file", "-f", help="文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径")
    
    args = parser.parse_args()
    
    config_manager = ConfigManager()
    
    if args.action == "show":
        config_manager.print_current_config()
    
    elif args.action == "export":
        config_manager.export_config(args.output)
    
    elif args.action == "import":
        if not args.file:
            print("错误: 导入配置需要指定文件路径 (--file)")
            return
        config_manager.import_config(args.file)
    
    elif args.action == "validate":
        config_manager.validate_config()
    
    elif args.action == "create-env":
        config_manager.create_env_file(args.output or ".env")
    
    elif args.action == "create-template":
        config_manager.create_config_template(args.output)
    
    elif args.action == "sources":
        config_manager.show_config_sources()


if __name__ == "__main__":
    main() 