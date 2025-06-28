#!/usr/bin/env python3
"""
Collect 模块使用示例
包含各种配置示例和测试用例
"""

import json
import sys
import os
import requests
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from hybrid_driver.collect import CollectItems

# HTTP测试配置
SERVER_URL = "http://localhost:8002"
SERIAL_ID = "172.16.1.125:6524"

def coffee_menu_example():
    """咖啡菜单采集示例"""
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {
                "selector": "body"
            },
            "options": {
                "item_selector": ".wx-menu-product",
                "close_dialog": True,
                "package": "com.lucky.luckyclient",
                "loading_view": "com.lucky.luckyclient:id/v_lottie",
                "dialog_views": [
                    "com.lucky.luckyclient:id/customPanel",
                    "com.lucky.luckyclient:id/webview_dialog"
                ],
                "singleton": False,
                "max_items": 20,
                "scroll_enabled": False,
                "timeout": 30
            }
        },
        "fields": {
            "name": {
                "selector": ".product--menu-product_name",
                "type": "text",
                "required": True,
                "description": "咖啡商品名称"
            },
            "price": {
                "selector": ".bar--discountPrice",
                "type": "text",
                "required": True,
                "description": "咖啡折扣价格"
            },
            "original_price": {
                "selector": ".bar--original",
                "type": "text",
                "description": "咖啡原价"
            },
            "description": {
                "selector": ".product--color-gray3",
                "type": "text",
                "description": "咖啡描述信息"
            }
        }
    }
    return config

def coffee_menu_selenium_optimized_example():
    """咖啡菜单采集示例 - Selenium优化版本"""
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {
                "selector": "body",
                "by": "css selector"
            },
            "options": {
                "item_selector": ".wx-menu-product",
                "item_by": "css selector",
                "close_dialog": True,
                "package": "com.lucky.luckyclient",
                "loading_view": "com.lucky.luckyclient:id/v_lottie",
                "dialog_views": [
                    "com.lucky.luckyclient:id/customPanel",
                    "com.lucky.luckyclient:id/webview_dialog"
                ],
                "singleton": False,
                "max_items": 20,
                "scroll_enabled": False,
                "timeout": 30,
                "wait_timeout": 10,
                "implicit_wait": 3,
                "page_load_timeout": 30
            }
        },
        "fields": {
            "name": {
                "selector": ".product--menu-product_name",
                "by": "css selector",
                "type": "text",
                "required": True,
                "description": "咖啡商品名称",
                "wait_visible": True
            },
            "price": {
                "selector": ".bar--discountPrice",
                "by": "css selector",
                "type": "text",
                "required": True,
                "description": "咖啡折扣价格",
                "regex": "\\D*([\\d.]+).*"
            },
            "original_price": {
                "selector": ".bar--original",
                "by": "css selector",
                "type": "text",
                "description": "咖啡原价"
            },
            "description": {
                "selector": ".product--color-gray3",
                "by": "css selector",
                "type": "text",
                "description": "咖啡描述信息"
            },
            "link": {
                "selector": "a",
                "by": "css selector",
                "type": "attribute",
                "attribute": "href",
                "description": "商品链接"
            },
            "image": {
                "selector": "img",
                "by": "css selector",
                "type": "attribute",
                "attribute": "src",
                "description": "商品图片"
            }
        }
    }
    return config

def xpath_example():
    """XPath定位方式示例"""
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {
                "selector": "//div[@class='product-list']",
                "by": "xpath"
            },
            "options": {
                "item_selector": "//div[@class='product-item']",
                "item_by": "xpath",
                "wait_timeout": 10,
                "implicit_wait": 3
            }
        },
        "fields": {
            "name": {
                "selector": "//h3[@class='product-name']",
                "by": "xpath",
                "type": "text",
                "required": True
            },
            "price": {
                "selector": "//span[@class='product-price']",
                "by": "xpath",
                "type": "text",
                "regex": "\\D*([\\d.]+).*"
            },
            "link": {
                "selector": "//a",
                "by": "xpath",
                "type": "attribute",
                "attribute": "href"
            }
        }
    }
    return config

def attribute_extraction_example():
    """属性提取示例"""
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {
                "selector": "body"
            },
            "options": {
                "item_selector": ".product-item"
            }
        },
        "fields": {
            "name": {
                "selector": ".product-name",
                "type": "text"
            },
            "price": {
                "selector": ".product-price",
                "type": "text"
            },
            "link": {
                "selector": "a",
                "type": "attribute",
                "attribute": "href"
            },
            "image": {
                "selector": "img",
                "type": "attribute",
                "attribute": "src"
            },
            "data_id": {
                "selector": ".product-item",
                "type": "attribute",
                "attribute": "data-id"
            },
            "title": {
                "selector": "img",
                "type": "attribute",
                "attribute": "title"
            },
            "alt": {
                "selector": "img",
                "type": "attribute",
                "attribute": "alt"
            }
        }
    }
    return config

def element_state_example():
    """元素状态检查示例"""
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {
                "selector": "body"
            },
            "options": {
                "item_selector": ".product-item"
            }
        },
        "fields": {
            "name": {
                "selector": ".product-name",
                "type": "text"
            },
            "price": {
                "selector": ".product-price",
                "type": "text"
            },
            "is_available": {
                "selector": ".stock-status",
                "type": "displayed",
                "description": "是否有库存"
            },
            "is_selected": {
                "selector": "input[type='checkbox']",
                "type": "checked",
                "description": "是否选中"
            },
            "is_visible": {
                "selector": ".product-image",
                "type": "displayed",
                "description": "图片是否可见"
            }
        }
    }
    return config

def wait_mechanism_example():
    """等待机制示例"""
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {
                "selector": "body"
            },
            "options": {
                "item_selector": ".product-item",
                "wait_timeout": 15,
                "implicit_wait": 5,
                "page_load_timeout": 60
            }
        },
        "fields": {
            "name": {
                "selector": ".product-name",
                "type": "text",
                "wait_visible": True
            },
            "price": {
                "selector": ".product-price",
                "type": "text",
                "wait_visible": True
            },
            "description": {
                "selector": ".product-desc",
                "type": "text",
                "wait_visible": False
            }
        }
    }
    return config

def shop_detail_example():
    """店铺详情采集示例"""
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {
                "selector": "com.lucky.luckyclient:id/ptr_classic_layout"
            },
            "options": {
                "close_dialog": True,
                "package": "com.lucky.luckyclient",
                "loading_view": "com.lucky.luckyclient:id/v_lottie",
                "dialog_views": [
                    "com.lucky.luckyclient:id/customPanel",
                    "com.lucky.luckyclient:id/webview_dialog",
                    "com.lucky.luckyclient:id/rl_orderDetailRoot",
                    "com.lucky.luckyclient:id/btnUpdateNow"
                ],
                "dialog_actions": [
                    "click#com.lucky.luckyclient:id/taskPushCloseBtn",
                    "click#com.lucky.luckyclient:id/iv_left_action_btn"
                ],
                "singleton": True,
                "required_fields": ["address", "dishes"]
            }
        },
        "fields": {
            "address": {
                "selector": "com.lucky.luckyclient:id/tv_store_detail_store_name",
                "type": "text",
                "required": True
            },
            "dishes": {
                "selector": "com.lucky.luckyclient:id/rv_goods",
                "type": "array",
                "fields": {
                    "name": {
                        "selector": "com.lucky.luckyclient:id/tv_product_name",
                        "type": "text"
                    },
                    "price": {
                        "selector": "com.lucky.luckyclient:id/tvPriceTop",
                        "type": "text",
                        "regex": "\\D*([\\d.]+).*"
                    }
                }
            }
        }
    }
    return config

def history_orders_example():
    """历史订单采集示例"""
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {
                "selector": "com.lucky.luckyclient:id/recycler_view"
            },
            "options": {
                "close_dialog": True,
                "package": "com.lucky.luckyclient",
                "loading_view": "com.lucky.luckyclient:id/v_lottie"
            }
        },
        "fields": {
            "type": {
                "selector": "com.lucky.luckyclient:id/tv_info_order_type",
                "type": "text"
            },
            "price": {
                "selector": "com.lucky.luckyclient:id/tv_order_total_price_2",
                "type": "text",
                "regex": "\\D*([\\d.]+).*"
            },
            "location": {
                "selector": "com.lucky.luckyclient:id/tv_order_dept_or_address",
                "type": "text"
            },
            "time": {
                "selector": "com.lucky.luckyclient:id/tv_order_create_time",
                "type": "text"
            },
            "status": {
                "selector": "com.lucky.luckyclient:id/tv_order_status",
                "type": "text"
            },
            "dishes": {
                "selector": "com.lucky.luckyclient:id/tv_order_product_name",
                "type": "array",
                "fields": {
                    "name": {
                        "selector": "com.lucky.luckyclient:id/tv_order_product_name",
                        "type": "text"
                    },
                    "count": {
                        "selector": "com.lucky.luckyclient:id/tv_product_count",
                        "type": "text",
                        "regex": "\\D*([\\d.]+).*"
                    },
                    "preference": {
                        "selector": "com.lucky.luckyclient:id/tv_product_addition",
                        "type": "text"
                    }
                }
            }
        }
    }
    return config

def search_dish_list_example():
    """搜索菜品列表采集示例"""
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {
                "selector": "com.lucky.luckyclient:id/recycler_view",
                "fallback": "com.lucky.luckyclient:id/search_empty"
            },
            "options": {
                "close_dialog": True,
                "package": "com.lucky.luckyclient",
                "loading_view": "com.lucky.luckyclient:id/v_lottie",
                "dialog_views": [
                    "com.lucky.luckyclient:id/customPanel",
                    "com.lucky.luckyclient:id/webview_dialog"
                ]
            }
        },
        "fields": {
            "name": {
                "selector": "com.lucky.luckyclient:id/tv_product_name",
                "type": "text"
            },
            "price": {
                "selector": "com.lucky.luckyclient:id/discount_price",
                "type": "text",
                "regex": "\\D*([\\d.]+).*"
            }
        }
    }
    return config

def templates_example():
    """配置模板示例"""
    templates = {
        "templates": {
            "shop_list": {
                "container": "com.lucky.luckyclient:id/recycler_view",
                "options": {
                    "close_dialog": True,
                    "package": "com.lucky.luckyclient",
                    "loading_view": "com.lucky.luckyclient:id/v_lottie"
                },
                "fields": {
                    "name": "com.lucky.luckyclient:id/tv_dept_name",
                    "location": "com.lucky.luckyclient:id/tv_dept_address",
                    "state": "com.lucky.luckyclient:id/shop_state_ico",
                    "work_time": "com.lucky.luckyclient:id/tv_work_time"
                }
            },
            "dish_list": {
                "container": "com.lucky.luckyclient:id/rv_goods",
                "options": {
                    "close_dialog": True,
                    "package": "com.lucky.luckyclient"
                },
                "fields": {
                    "name": "com.lucky.luckyclient:id/tv_product_name",
                    "price": {
                        "selector": "com.lucky.luckyclient:id/tvPriceTop",
                        "regex": "\\D*([\\d.]+).*"
                    }
                }
            },
            "order_list": {
                "container": "com.lucky.luckyclient:id/recycler_view",
                "options": {
                    "close_dialog": True,
                    "package": "com.lucky.luckyclient"
                },
                "fields": {
                    "type": "com.lucky.luckyclient:id/tv_info_order_type",
                    "price": {
                        "selector": "com.lucky.luckyclient:id/tv_order_total_price_2",
                        "regex": "\\D*([\\d.]+).*"
                    },
                    "location": "com.lucky.luckyclient:id/tv_order_dept_or_address",
                    "time": "com.lucky.luckyclient:id/tv_order_create_time",
                    "status": "com.lucky.luckyclient:id/tv_order_status"
                }
            }
        }
    }
    return templates

def performance_optimization_example():
    """性能优化配置示例"""
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {
                "selector": "body"
            },
            "options": {
                "item_selector": ".wx-menu-product",
                "close_dialog": True,
                "package": "com.lucky.luckyclient",
                "max_items": 20,
                "scroll_enabled": False,
                "timeout": 30
            }
        },
        "cache": {
            "enabled": True,
            "ttl": 3600,
            "key_pattern": "config_{hash}"
        },
        "batch": {
            "enabled": True,
            "max_concurrent": 5,
            "timeout": 30
        },
        "retry": {
            "max_attempts": 3,
            "backoff": "exponential",
            "conditions": ["element_not_found", "timeout"]
        },
        "fields": {
            "name": {
                "selector": ".product--menu-product_name",
                "type": "text",
                "required": True
            },
            "price": {
                "selector": ".bar--discountPrice",
                "type": "text",
                "required": True
            }
        }
    }
    return config

def convert_legacy_config(legacy_command):
    """将旧格式命令转换为新格式"""
    
    # 解析旧格式
    parts = legacy_command.split()
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {"options": {}, "filters": {}},
        "fields": {}
    }
    
    # 解析参数
    for part in parts:
        if part.startswith("--"):
            key, value = part[2:].split("=", 1)
            if key == "id":
                config["config"]["container"] = {"selector": value}
            elif key == "pkg":
                config["config"]["options"]["package"] = value
            elif key == "close_dialog":
                config["config"]["options"]["close_dialog"] = value == "1"
            elif key == "loading_view":
                config["config"]["options"]["loading_view"] = value
            elif key == "dialog_view":
                config["config"]["options"]["dialog_views"] = value.split("||")
            elif key == "singleton":
                config["config"]["options"]["singleton"] = value == "1"
            elif key == "important_fields":
                config["config"]["filters"]["required_fields"] = value.split(",")
    
    # 解析字段
    field_parts = parts[-1].split(",")
    for field_part in field_parts:
        if "=" in field_part:
            field_name, selector = field_part.split("=", 1)
            config["fields"][field_name] = {
                "selector": selector,
                "type": "text"
            }
    
    return config

def test_collector_creation():
    """测试采集器创建"""
    try:
        # 测试咖啡菜单配置
        coffee_config = coffee_menu_example()
        collector = CollectItems(config_json=json.dumps(coffee_config))
        print("✅ 咖啡菜单采集器创建成功")
        
        # 测试Selenium优化配置
        selenium_config = coffee_menu_selenium_optimized_example()
        collector = CollectItems(config_json=json.dumps(selenium_config))
        print("✅ Selenium优化采集器创建成功")
        
        # 测试XPath配置
        xpath_config = xpath_example()
        collector = CollectItems(config_json=json.dumps(xpath_config))
        print("✅ XPath采集器创建成功")
        
        # 测试属性提取配置
        attr_config = attribute_extraction_example()
        collector = CollectItems(config_json=json.dumps(attr_config))
        print("✅ 属性提取采集器创建成功")
        
        # 测试元素状态配置
        state_config = element_state_example()
        collector = CollectItems(config_json=json.dumps(state_config))
        print("✅ 元素状态采集器创建成功")
        
        # 测试等待机制配置
        wait_config = wait_mechanism_example()
        collector = CollectItems(config_json=json.dumps(wait_config))
        print("✅ 等待机制采集器创建成功")
        
        # 测试店铺详情配置
        shop_config = shop_detail_example()
        collector = CollectItems(config_json=json.dumps(shop_config))
        print("✅ 店铺详情采集器创建成功")
        
        # 测试历史订单配置
        order_config = history_orders_example()
        collector = CollectItems(config_json=json.dumps(order_config))
        print("✅ 历史订单采集器创建成功")
        
        print("✅ 所有采集器创建测试通过")
        return True
    except Exception as e:
        print(f"❌ 采集器创建测试失败: {e}")
        return False

def test_legacy_conversion():
    """测试旧格式转换"""
    try:
        # 旧格式命令
        legacy_command = """ACTION_COLLECT_ITEM_INFO --close_dialog=1 --pkg=com.lucky.luckyclient --id=com.lucky.luckyclient:id/recycler_view --loading_view=com.lucky.luckyclient:id/v_lottie name=com.lucky.luckyclient:id/tv_product_name,price=com.lucky.luckyclient:id/discount_price"""
        
        # 转换为新格式
        new_config = convert_legacy_config(legacy_command)
        
        # 验证转换结果
        assert new_config["action"] == "ACTION_COLLECT_ITEM_INFO"
        assert new_config["config"]["container"]["selector"] == "com.lucky.luckyclient:id/recycler_view"
        assert new_config["config"]["options"]["package"] == "com.lucky.luckyclient"
        assert new_config["config"]["options"]["close_dialog"] == True
        assert "name" in new_config["fields"]
        assert "price" in new_config["fields"]
        
        print("✅ 旧格式转换测试通过")
        return True
    except Exception as e:
        print(f"❌ 旧格式转换测试失败: {e}")
        return False

def test_http_coffee_collection():
    """测试HTTP接口咖啡信息收集"""
    print("☕ 测试HTTP接口咖啡信息收集...")
    
    # 连接设备
    if not connect_device():
        return False
    
    # 使用咖啡菜单配置
    config = coffee_menu_example()
    
    # 发送请求
    request_data = {
        "serial_id": SERIAL_ID,
        "config_json": json.dumps(config)
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/collect_items",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("✅ HTTP接口咖啡信息收集成功")
                
                # 解析并显示结果
                data = result.get("data", {})
                items = data.get("items", [])
                
                if isinstance(items, list):
                    print(f"🎉 共收集到 {len(items)} 个咖啡商品:")
                    for i, coffee in enumerate(items, 1):
                        print(f"{i:2d}. {coffee.get('name', 'N/A')} - ￥{coffee.get('price', 'N/A')}")
                        if coffee.get('original_price'):
                            print(f"     📉 原价: ￥{coffee['original_price']}")
                        if coffee.get('description'):
                            print(f"     📝 描述: {coffee['description']}")
                        print("")
                else:
                    print(f"📊 收集到的数据: {items}")
                
                return True
            else:
                print(f"❌ HTTP接口咖啡信息收集失败: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_http_config_file():
    """测试HTTP接口配置文件方式"""
    print("📄 测试HTTP接口配置文件方式...")
    
    # 连接设备
    if not connect_device():
        return False
    
    # 使用配置文件
    request_data = {
        "serial_id": SERIAL_ID,
        "config_file": "coffee_menu_config.json"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/collect_items",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("✅ HTTP接口配置文件方式收集成功")
                
                # 解析并显示结果
                data = result.get("data", {})
                items = data.get("items", [])
                
                if isinstance(items, list):
                    print(f"🎉 共收集到 {len(items)} 个咖啡商品:")
                    for i, coffee in enumerate(items, 1):
                        print(f"{i:2d}. {coffee.get('name', 'N/A')} - ￥{coffee.get('price', 'N/A')}")
                        if coffee.get('original_price'):
                            print(f"     📉 原价: ￥{coffee['original_price']}")
                        if coffee.get('description'):
                            print(f"     📝 描述: {coffee['description']}")
                        print("")
                else:
                    print(f"📊 收集到的数据: {items}")
                
                return True
            else:
                print(f"❌ HTTP接口配置文件方式收集失败: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_http_legacy_compatibility():
    """测试HTTP接口向后兼容性"""
    print("🔄 测试HTTP接口向后兼容性...")
    
    # 连接设备
    if not connect_device():
        return False
    
    # 老协议参数
    request_data = {
        "serial_id": SERIAL_ID,
        "container_selector": "com.lucky.luckyclient:id/recycler_view",
        "item_selectors": {
            "name": "com.lucky.luckyclient:id/tv_product_name",
            "price": "com.lucky.luckyclient:id/tvPriceTop"
        },
        "options": {
            "close_dialog": True,
            "package": "com.lucky.luckyclient"
        },
        "filters": {
            "required_fields": ["name", "price"]
        }
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/collect_items",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("✅ HTTP接口向后兼容性测试成功")
                return True
            else:
                print(f"❌ HTTP接口向后兼容性测试失败: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def connect_device():
    """连接设备"""
    connect_data = {
        "serial_id": SERIAL_ID
    }
    
    try:
        connect_response = requests.post(
            f"{SERVER_URL}/connect",
            json=connect_data,
            timeout=30
        )
        
        if connect_response.status_code != 200:
            print(f"❌ 设备连接失败: {connect_response.status_code}")
            return False
            
        connect_result = connect_response.json()
        if connect_result.get("code") != 0:
            print(f"❌ 设备连接失败: {connect_result.get('message')}")
            return False
            
        print("✅ 设备连接成功")
        return True
    except Exception as e:
        print(f"❌ 设备连接异常: {e}")
        return False

def test_server_connection():
    """测试服务器连接"""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
            return True
        else:
            print("❌ 服务器连接失败")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

if __name__ == "__main__":
    print("开始测试 Collect 模块示例...")
    print("=" * 50)
    
    # 测试采集器创建
    test_collector_creation()
    print()
    
    # 测试旧格式转换
    test_legacy_conversion()
    print()
    
    # 测试服务器连接
    if test_server_connection():
        print("\n" + "=" * 50)
        print("HTTP接口测试")
        print("=" * 50)
        
        # HTTP接口测试
        http_tests = [
            ("咖啡信息收集", test_http_coffee_collection),
            ("配置文件方式", test_http_config_file),
            ("向后兼容性", test_http_legacy_compatibility)
        ]
        
        results = []
        for test_name, test_func in http_tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                results.append((test_name, False))
        
        # 输出HTTP测试结果
        print("\n" + "=" * 50)
        print("HTTP测试结果汇总:")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n总计: {passed}/{total} HTTP测试通过")
        
        if passed == total:
            print("🎉 所有HTTP测试通过！")
        else:
            print("⚠️  部分HTTP测试失败，需要检查实现")
    else:
        print("⚠️  服务器未连接，跳过HTTP接口测试")
    
    print("\n示例测试完成！") 