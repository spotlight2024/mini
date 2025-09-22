#!/usr/bin/env python3
"""
优化版淘宝搜索API测试脚本
验证代理获取、性能指标等功能
"""
import asyncio
import time
import requests
import json
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:10001/test/taobao"
TEST_IMAGE = "logo.png"

def test_health_check():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data['status']}")
            print(f"   服务: {data['service']}")
            print(f"   版本: {data['version']}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_metrics():
    """测试性能指标"""
    print("\n📊 测试性能指标...")
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 性能指标获取成功:")
            print(f"   代理获取模式: {data['proxy_fetch_mode']}")
            print(f"   缓存状态: {data['cache_enabled']}")
            print(f"   时间戳: {data['timestamp']}")
            return True
        else:
            print(f"❌ 性能指标获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 性能指标获取异常: {e}")
        return False

def test_legacy_api():
    """测试兼容接口"""
    print("\n🔄 测试兼容接口...")
    try:
        params = {
            "uid": "test_user_legacy",
            "image_path": TEST_IMAGE,
            "timeout": 60,
            "proxy_provider": "tianqi"
        }
        
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/search", params=params)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 兼容接口测试成功 (耗时: {duration:.2f}秒)")
            print(f"   状态: {data['status']}")
            print(f"   代理信息: {data.get('proxy_info', 'N/A')}")
            print(f"   性能指标: {data.get('performance_metrics', {})}")
            return True
        else:
            print(f"❌ 兼容接口测试失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 兼容接口测试异常: {e}")
        return False

def test_optimized_api():
    """测试优化接口"""
    print("\n🚀 测试优化接口...")
    try:
        payload = {
            "uid": "test_user_optimized",
            "image_path": TEST_IMAGE,
            "timeout": 60,
            "proxy_provider": "tianqi",
            "enable_cache": False,  # 禁用缓存，每次都获取最新代理
            "max_retries": 3
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/search", 
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 优化接口测试成功 (耗时: {duration:.2f}秒)")
            print(f"   状态: {data['status']}")
            print(f"   会话ID: {data['session_id']}")
            print(f"   代理信息: {data.get('proxy_info', 'N/A')}")
            print(f"   性能指标: {data.get('performance_metrics', {})}")
            print(f"   商品数量: {data.get('product_count', 0)}")
            return True
        else:
            print(f"❌ 优化接口测试失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 优化接口测试异常: {e}")
        return False

def test_proxy_providers():
    """测试不同代理提供者"""
    print("\n🌐 测试不同代理提供者...")
    
    providers = ["tianqi", "juliang", "kuai"]
    results = {}
    
    for provider in providers:
        print(f"\n   测试 {provider} 代理...")
        try:
            payload = {
                "uid": f"test_user_{provider}",
                "image_path": TEST_IMAGE,
                "timeout": 30,
                "proxy_provider": provider,
                "enable_cache": False
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/search", 
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                proxy_info = data.get('proxy_info', {})
                print(f"   ✅ {provider} 代理测试成功 (耗时: {duration:.2f}秒)")
                print(f"      IP: {proxy_info.get('ip', 'N/A')}")
                print(f"      端口: {proxy_info.get('port', 'N/A')}")
                results[provider] = {"success": True, "duration": duration}
            else:
                print(f"   ❌ {provider} 代理测试失败: {response.status_code}")
                results[provider] = {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"   ❌ {provider} 代理测试异常: {e}")
            results[provider] = {"success": False, "error": str(e)}
    
    return results

def test_concurrent_requests():
    """测试并发请求"""
    print("\n⚡ 测试并发请求...")
    
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def single_request(request_id: int):
        """单个请求"""
        try:
            payload = {
                "uid": f"concurrent_user_{request_id}",
                "image_path": TEST_IMAGE,
                "timeout": 30,
                "proxy_provider": "tianqi",
                "enable_cache": False
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/search", 
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "request_id": request_id,
                    "success": True,
                    "duration": duration,
                    "proxy_ip": data.get('proxy_info', {}).get('ip', 'N/A')
                }
            else:
                return {
                    "request_id": request_id,
                    "success": False,
                    "error": response.text,
                    "duration": duration
                }
        except Exception as e:
            return {
                "request_id": request_id,
                "success": False,
                "error": str(e),
                "duration": 0
            }
    
    # 执行5个并发请求
    concurrent_count = 5
    print(f"   启动 {concurrent_count} 个并发请求...")
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
        futures = [executor.submit(single_request, i) for i in range(concurrent_count)]
        results = [future.result() for future in as_completed(futures)]
    
    total_duration = time.time() - start_time
    
    # 统计结果
    success_count = sum(1 for r in results if r['success'])
    avg_duration = sum(r['duration'] for r in results if r['success']) / max(success_count, 1)
    
    print(f"   ✅ 并发测试完成:")
    print(f"      总耗时: {total_duration:.2f}秒")
    print(f"      成功请求: {success_count}/{concurrent_count}")
    print(f"      平均响应时间: {avg_duration:.2f}秒")
    
    # 显示每个请求的代理IP（验证每次都获取新IP）
    print(f"   代理IP分布:")
    for result in results:
        if result['success']:
            print(f"      请求{result['request_id']}: {result['proxy_ip']}")
    
    return success_count == concurrent_count

def main():
    """主测试函数"""
    print("🧪 开始测试优化版淘宝搜索API")
    print("=" * 50)
    
    test_results = {}
    
    # 1. 健康检查
    test_results['health'] = test_health_check()
    
    # 2. 性能指标
    test_results['metrics'] = test_metrics()
    
    # 3. 兼容接口测试
    test_results['legacy'] = test_legacy_api()
    
    # 4. 优化接口测试
    test_results['optimized'] = test_optimized_api()
    
    # 5. 代理提供者测试
    test_results['proxy_providers'] = test_proxy_providers()
    
    # 6. 并发测试
    test_results['concurrent'] = test_concurrent_requests()
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 测试结果总结:")
    print("=" * 50)
    
    for test_name, result in test_results.items():
        if test_name == 'proxy_providers':
            print(f"🌐 代理提供者测试:")
            for provider, provider_result in result.items():
                status = "✅" if provider_result['success'] else "❌"
                print(f"   {provider}: {status}")
        else:
            status = "✅" if result else "❌"
            print(f"{test_name}: {status}")
    
    # 总体评估
    passed_tests = sum(1 for r in test_results.values() if r is True or (isinstance(r, dict) and any(v.get('success', False) for v in r.values())))
    total_tests = len(test_results)
    
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！优化版API工作正常")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")

if __name__ == "__main__":
    main()
