#!/usr/bin/env python3
"""
API测试脚本 - 验证新的模块化API结构
"""
import requests
import json
import time
from typing import Dict, Any


class APITester:
    """API测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self) -> bool:
        """测试健康检查接口"""
        print("测试健康检查接口...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✓ 健康检查通过")
                return True
            else:
                print(f"✗ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 健康检查异常: {e}")
            return False
    
    def test_device_connect(self, serial_id: str = "test_device") -> bool:
        """测试设备连接接口"""
        print("测试设备连接接口...")
        try:
            response = self.session.post(
                f"{self.base_url}/device/connect",
                json={"serial_id": serial_id}
            )
            print(f"响应: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"✗ 设备连接测试异常: {e}")
            return False
    
    def test_element_find(self, serial_id: str = "test_device") -> bool:
        """测试元素查找接口"""
        print("测试元素查找接口...")
        try:
            response = self.session.post(
                f"{self.base_url}/element/find",
                json={
                    "serial_id": serial_id,
                    "method": "css selector",
                    "selector": ".test-class"
                }
            )
            print(f"响应: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"✗ 元素查找测试异常: {e}")
            return False
    
    def test_mock_click(self, serial_id: str = "test_device") -> bool:
        """测试模拟点击接口"""
        print("测试模拟点击接口...")
        try:
            response = self.session.post(
                f"{self.base_url}/mock/click",
                json={
                    "serial_id": serial_id,
                    "method": "css selector",
                    "selector": ".test-button"
                }
            )
            print(f"响应: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"✗ 模拟点击测试异常: {e}")
            return False
    
    def test_page_check(self, serial_id: str = "test_device") -> bool:
        """测试页面检查接口"""
        print("测试页面检查接口...")
        try:
            response = self.session.post(
                f"{self.base_url}/page/check",
                json={
                    "serial_id": serial_id,
                    "required_page": "Home"
                }
            )
            print(f"响应: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"✗ 页面检查测试异常: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("=" * 50)
        print("开始API测试...")
        print("=" * 50)
        
        results = {}
        
        # 测试健康检查
        results["health"] = self.test_health()
        print()
        
        # 测试设备连接
        results["device_connect"] = self.test_device_connect()
        print()
        
        # 测试元素查找
        results["element_find"] = self.test_element_find()
        print()
        
        # 测试模拟点击
        results["mock_click"] = self.test_mock_click()
        print()
        
        # 测试页面检查
        results["page_check"] = self.test_page_check()
        print()
        
        # 输出测试结果
        print("=" * 50)
        print("测试结果汇总:")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n总计: {passed}/{total} 个测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！")
        else:
            print("⚠️  部分测试失败，请检查服务器状态")
        
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API测试脚本")
    parser.add_argument("--url", default="http://localhost:8000", help="API服务器地址")
    
    args = parser.parse_args()
    
    tester = APITester(args.url)
    results = tester.run_all_tests()
    
    # 返回适当的退出码
    exit_code = 0 if all(results.values()) else 1
    exit(exit_code)


if __name__ == "__main__":
    main() 