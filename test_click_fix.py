#!/usr/bin/env python3
"""
测试 click 接口修复的脚本
"""
import requests
import json

def test_click_api():
    """测试 click 接口"""
    url = "http://localhost:8001/element/click"
    
    # 测试数据
    test_data = {
        "serial_id": "47.94.130.125:6521",
        "method": "css selector",
        "selector": "button.search-button",
        "timeout": 10,
        "wait_for_new_window": False
    }
    
    print("测试 click 接口...")
    print(f"请求数据: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("✅ click 接口测试成功")
            else:
                print(f"❌ click 接口返回错误: {result.get('message')}")
        else:
            print(f"❌ HTTP 请求失败: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
    except Exception as e:
        print(f"❌ 其他异常: {e}")

def test_connect_api():
    """测试 connect 接口"""
    url = "http://localhost:8001/device/connect"
    
    test_data = {
        "serial_id": "47.94.130.125:6521",
        "user_id": "test_user",
        "android_process": "com.tencent.mm:appbrand0"
    }
    
    print("\n测试 connect 接口...")
    print(f"请求数据: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("✅ connect 接口测试成功")
            else:
                print(f"❌ connect 接口返回错误: {result.get('message')}")
        else:
            print(f"❌ HTTP 请求失败: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
    except Exception as e:
        print(f"❌ 其他异常: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("开始测试 API 修复")
    print("=" * 50)
    
    # 先测试 connect 接口
    test_connect_api()
    
    # 再测试 click 接口
    test_click_api()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50) 