# 老协议到新协议的映射实现

## HistoryOrders页面配置转换示例

### 原始老协议
```bash
ACTION_COLLECT_ITEM_INFO --close_dialog=1 --pkg=com.lucky.luckyclient --id=com.lucky.luckyclient:id/recycler_view --loading_view=com.lucky.luckyclient:id/v_lottie type=com.lucky.luckyclient:id/tv_info_order_type,view:price:regex#\\D*([\\d.]+).*=com.lucky.luckyclient:id/tv_order_total_price_2,location=com.lucky.luckyclient:id/tv_order_dept_or_address,time=com.lucky.luckyclient:id/tv_order_create_time,status=com.lucky.luckyclient:id/tv_order_status,[view:name:flatten#dishes]=com.lucky.luckyclient:id/tv_order_product_name,[view:cnt:flatten#dishes:regex#\\D*([\\d.]+).*]=com.lucky.luckyclient:id/tv_product_count,[view:prefer:flatten#dishes]=com.lucky.luckyclient:id/tv_product_addition
```

## 方案一：JSON配置文件（推荐）

### 1.1 完整JSON配置
```json
{
  "action": "ACTION_COLLECT_ITEM_INFO",
  "config": {
    "container": {
      "selector": "com.lucky.luckyclient:id/recycler_view"
    },
    "options": {
      "close_dialog": true,
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
```

### 1.2 使用配置文件
```bash
# 方式1：使用配置文件
ACTION_COLLECT_ITEM_INFO --config=history_orders.json

# 方式2：内联JSON配置
ACTION_COLLECT_ITEM_INFO --config='{"action":"ACTION_COLLECT_ITEM_INFO","config":{"container":{"selector":"com.lucky.luckyclient:id/recycler_view"},"options":{"close_dialog":true,"package":"com.lucky.luckyclient","loading_view":"com.lucky.luckyclient:id/v_lottie"}},"fields":{"type":{"selector":"com.lucky.luckyclient:id/tv_info_order_type","type":"text"},"price":{"selector":"com.lucky.luckyclient:id/tv_order_total_price_2","type":"text","regex":"\\D*([\\d.]+).*"},"location":{"selector":"com.lucky.luckyclient:id/tv_order_dept_or_address","type":"text"},"time":{"selector":"com.lucky.luckyclient:id/tv_order_create_time","type":"text"},"status":{"selector":"com.lucky.luckyclient:id/tv_order_status","type":"text"},"dishes":{"selector":"com.lucky.luckyclient:id/tv_order_product_name","type":"array","fields":{"name":{"selector":"com.lucky.luckyclient:id/tv_order_product_name","type":"text"},"count":{"selector":"com.lucky.luckyclient:id/tv_product_count","type":"text","regex":"\\D*([\\d.]+).*"},"preference":{"selector":"com.lucky.luckyclient:id/tv_product_addition","type":"text"}}}}}'
```

## 方案二：改进的命令行语法

### 2.1 分组参数格式
```bash
ACTION_COLLECT_ITEM_INFO \
  --container="com.lucky.luckyclient:id/recycler_view" \
  --package="com.lucky.luckyclient" \
  --options="close_dialog=true,loading_view=com.lucky.luckyclient:id/v_lottie" \
  --fields="type:com.lucky.luckyclient:id/tv_info_order_type,price:com.lucky.luckyclient:id/tv_order_total_price_2:regex#\\D*([\\d.]+).*,location:com.lucky.luckyclient:id/tv_order_dept_or_address,time:com.lucky.luckyclient:id/tv_order_create_time,status:com.lucky.luckyclient:id/tv_order_status,dishes:com.lucky.luckyclient:id/tv_order_product_name:array[name:com.lucky.luckyclient:id/tv_order_product_name,count:com.lucky.luckyclient:id/tv_product_count:regex#\\D*([\\d.]+).*,preference:com.lucky.luckyclient:id/tv_product_addition]"
```

### 2.2 简化字段语法
```bash
ACTION_COLLECT_ITEM_INFO \
  --container="com.lucky.luckyclient:id/recycler_view" \
  --package="com.lucky.luckyclient" \
  --options="close_dialog=true,loading_view=com.lucky.luckyclient:id/v_lottie" \
  --fields="type:com.lucky.luckyclient:id/tv_info_order_type,price:com.lucky.luckyclient:id/tv_order_total_price_2:regex#\\D*([\\d.]+).*,location:com.lucky.luckyclient:id/tv_order_dept_or_address,time:com.lucky.luckyclient:id/tv_order_create_time,status:com.lucky.luckyclient:id/tv_order_status" \
  --array_fields="dishes:com.lucky.luckyclient:id/tv_order_product_name[name:com.lucky.luckyclient:id/tv_order_product_name,count:com.lucky.luckyclient:id/tv_product_count:regex#\\D*([\\d.]+).*,preference:com.lucky.luckyclient:id/tv_product_addition]"
```

## 方案三：模板化配置

### 3.1 定义订单列表模板
```json
{
  "templates": {
    "order_list": {
      "container": "com.lucky.luckyclient:id/recycler_view",
      "options": {
        "close_dialog": true,
        "package": "com.lucky.luckyclient",
        "loading_view": "com.lucky.luckyclient:id/v_lottie"
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
      },
      "arrays": {
        "dishes": {
          "selector": "com.lucky.luckyclient:id/tv_order_product_name",
          "fields": {
            "name": "com.lucky.luckyclient:id/tv_order_product_name",
            "count": {
              "selector": "com.lucky.luckyclient:id/tv_product_count",
              "regex": "\\D*([\\d.]+).*"
            },
            "preference": "com.lucky.luckyclient:id/tv_product_addition"
          }
        }
      }
    }
  }
}
```

### 3.2 使用模板
```bash
# 使用预定义模板
ACTION_COLLECT_ITEM_INFO --template=order_list

# 使用模板并覆盖部分配置
ACTION_COLLECT_ITEM_INFO --template=order_list --container="com.lucky.luckyclient:id/custom_recycler_view"
```

## 协议映射规则详解

### 1. 参数映射

| 老协议参数 | 新协议参数 | 说明 |
|-----------|-----------|------|
| `--id=<selector>` | `--container=<selector>` | 容器选择器 |
| `--pkg=<package>` | `--package=<package>` | 包名 |
| `--close_dialog=1` | `--options="close_dialog=true"` | 弹窗处理 |
| `--loading_view=<view>` | `--options="loading_view=<view>"` | 加载视图 |

### 2. 字段映射

#### 2.1 简单字段
```bash
# 老协议
type=com.lucky.luckyclient:id/tv_info_order_type

# 新协议 - JSON
"type": {
  "selector": "com.lucky.luckyclient:id/tv_info_order_type",
  "type": "text"
}

# 新协议 - 命令行
--fields="type:com.lucky.luckyclient:id/tv_info_order_type"
```

#### 2.2 带正则表达式的字段
```bash
# 老协议
view:price:regex#\\D*([\\d.]+).*=com.lucky.luckyclient:id/tv_order_total_price_2

# 新协议 - JSON
"price": {
  "selector": "com.lucky.luckyclient:id/tv_order_total_price_2",
  "type": "text",
  "regex": "\\D*([\\d.]+).*"
}

# 新协议 - 命令行
--fields="price:com.lucky.luckyclient:id/tv_order_total_price_2:regex#\\D*([\\d.]+).*"
```

#### 2.3 扁平化数组字段
```bash
# 老协议
[view:name:flatten#dishes]=com.lucky.luckyclient:id/tv_order_product_name

# 新协议 - JSON
"dishes": {
  "selector": "com.lucky.luckyclient:id/tv_order_product_name",
  "type": "array",
  "fields": {
    "name": {
      "selector": "com.lucky.luckyclient:id/tv_order_product_name",
      "type": "text"
    }
  }
}

# 新协议 - 命令行
--array_fields="dishes:com.lucky.luckyclient:id/tv_order_product_name[name:com.lucky.luckyclient:id/tv_order_product_name]"
```

## 自动转换工具

### Python转换脚本
```python
#!/usr/bin/env python3
import json
import re
import sys

def parse_legacy_field(field_def):
    """解析老协议的字段定义"""
    if '=' not in field_def:
        return None
    
    field_name, selector = field_def.split('=', 1)
    
    # 解析复杂字段定义
    if field_name.startswith('[') and field_name.endswith(']'):
        # 扁平化数组字段
        parts = field_name[1:-1].split(':')
        if len(parts) >= 4 and parts[2] == 'flatten':
            array_name = parts[3]
            field_type = parts[1] if len(parts) > 1 else 'text'
            regex = None
            
            # 检查是否有正则表达式
            if 'regex#' in field_name:
                regex_match = re.search(r'regex#([^:]+)', field_name)
                if regex_match:
                    regex = regex_match.group(1)
            
            return {
                'type': 'array',
                'array_name': array_name,
                'field_type': field_type,
                'selector': selector,
                'regex': regex
            }
    else:
        # 简单字段
        parts = field_name.split(':')
        field_type = parts[0] if len(parts) > 1 else 'text'
        actual_field_name = parts[1] if len(parts) > 1 else parts[0]
        regex = None
        
        # 检查是否有正则表达式
        if 'regex#' in field_name:
            regex_match = re.search(r'regex#([^:]+)', field_name)
            if regex_match:
                regex = regex_match.group(1)
        
        return {
            'type': 'simple',
            'field_name': actual_field_name,
            'field_type': field_type,
            'selector': selector,
            'regex': regex
        }

def convert_legacy_command(legacy_command):
    """将老协议命令转换为新协议JSON配置"""
    
    config = {
        "action": "ACTION_COLLECT_ITEM_INFO",
        "config": {
            "container": {},
            "options": {}
        },
        "fields": {}
    }
    
    # 解析命令参数
    parts = legacy_command.split()
    field_definitions = []
    
    for part in parts:
        if part.startswith('--'):
            if '=' in part:
                key, value = part[2:].split('=', 1)
                if key == 'id':
                    config['config']['container']['selector'] = value
                elif key == 'pkg':
                    config['config']['options']['package'] = value
                elif key == 'close_dialog':
                    config['config']['options']['close_dialog'] = value == '1'
                elif key == 'loading_view':
                    config['config']['options']['loading_view'] = value
        else:
            # 收集字段定义
            field_definitions.extend(part.split(','))
    
    # 解析字段定义
    arrays = {}
    
    for field_def in field_definitions:
        if not field_def.strip():
            continue
            
        parsed = parse_legacy_field(field_def.strip())
        if not parsed:
            continue
        
        if parsed['type'] == 'array':
            # 处理数组字段
            array_name = parsed['array_name']
            if array_name not in arrays:
                arrays[array_name] = {
                    'selector': parsed['selector'],
                    'type': 'array',
                    'fields': {}
                }
            
            field_name = parsed['field_type']
            field_config = {
                'selector': parsed['selector'],
                'type': 'text'
            }
            
            if parsed['regex']:
                field_config['regex'] = parsed['regex']
            
            arrays[array_name]['fields'][field_name] = field_config
        else:
            # 处理简单字段
            field_config = {
                'selector': parsed['selector'],
                'type': 'text'
            }
            
            if parsed['regex']:
                field_config['regex'] = parsed['regex']
            
            config['fields'][parsed['field_name']] = field_config
    
    # 添加数组字段
    config['fields'].update(arrays)
    
    return config

def main():
    if len(sys.argv) != 2:
        print("Usage: python convert_legacy.py <legacy_command>")
        sys.exit(1)
    
    legacy_command = sys.argv[1]
    new_config = convert_legacy_command(legacy_command)
    
    print("转换结果:")
    print(json.dumps(new_config, indent=2, ensure_ascii=False))
    
    # 生成新协议命令
    print("\n新协议命令:")
    print(f"ACTION_COLLECT_ITEM_INFO --config='{json.dumps(new_config, ensure_ascii=False)}'")

if __name__ == "__main__":
    main()
```

### 使用转换工具
```bash
# 转换HistoryOrders配置
python convert_legacy.py "ACTION_COLLECT_ITEM_INFO --close_dialog=1 --pkg=com.lucky.luckyclient --id=com.lucky.luckyclient:id/recycler_view --loading_view=com.lucky.luckyclient:id/v_lottie type=com.lucky.luckyclient:id/tv_info_order_type,view:price:regex#\\D*([\\d.]+).*=com.lucky.luckyclient:id/tv_order_total_price_2,location=com.lucky.luckyclient:id/tv_order_dept_or_address,time=com.lucky.luckyclient:id/tv_order_create_time,status=com.lucky.luckyclient:id/tv_order_status,[view:name:flatten#dishes]=com.lucky.luckyclient:id/tv_order_product_name,[view:cnt:flatten#dishes:regex#\\D*([\\d.]+).*]=com.lucky.luckyclient:id/tv_product_count,[view:prefer:flatten#dishes]=com.lucky.luckyclient:id/tv_product_addition"
```

## 实施建议

### 1. 渐进式迁移策略
1. **第一阶段**：实现自动转换工具，支持老协议到新协议的转换
2. **第二阶段**：在新功能中使用新协议格式
3. **第三阶段**：逐步迁移现有配置
4. **第四阶段**：完全切换到新协议（可选）

### 2. 兼容性保证
- 保持老协议解析器继续工作
- 提供自动转换工具
- 支持混合使用（老协议和新协议并存）

### 3. 最佳实践
- 优先使用JSON配置文件，提升可读性
- 对于简单配置，可以使用改进的命令行语法
- 对于重复配置，使用模板化方案
- 定期使用转换工具验证配置正确性

## 总结

通过以上方案，可以完全实现老协议的功能，同时获得更好的可读性、可维护性和扩展性。推荐采用JSON配置文件方案，配合自动转换工具，实现平滑的协议升级。 