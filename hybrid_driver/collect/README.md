# Collect 模块

元素信息采集模块，支持结构化JSON配置和多种采集模式，**针对 Selenium WebDriver 进行了深度优化**。

## 功能特性

- ✅ **结构化JSON配置**: 使用清晰的JSON格式定义采集规则
- ✅ **向后兼容**: 支持旧版参数格式，平滑迁移
- ✅ **多种采集模式**: 支持Web端和Native端元素采集
- ✅ **弹窗处理**: 自动处理各种弹窗和对话框
- ✅ **字段验证**: 支持必填字段验证和数据类型转换
- ✅ **性能优化**: 支持缓存、批量处理、重试机制
- ✅ **Selenium优化**: 深度集成 Selenium WebDriver，支持多种定位方式和等待机制

## 核心概念

### Container vs Item Selector 关系

这是采集系统的核心概念，理解它们的关系对于正确配置至关重要：

#### 📋 **概念定义**

| 概念 | 作用 | 示例 |
|------|------|------|
| **Container** | 定义采集的**页面区域范围** | `"body"`, `"#main-content"` |
| **Item Selector** | 在容器内**精确定位每个商品/项目** | `".product-item"`, `".menu-item"` |
| **Fields** | 在每个商品项内**提取具体数据** | `".product-name"`, `".product-price"` |

#### 🔍 **工作流程**

```
页面 → 找到Container → 在Container内找到Items → 对每个Item提取Fields
```

#### 📝 **HTML结构示例**

```html
<body>                    <!-- ← Container: "body" -->
    <div class="header">...</div>
    
    <div class="product-list">
        <div class="product-item">  <!-- ← Item: ".product-item" -->
            <h3 class="product-name">美式咖啡</h3>      <!-- ← Field: ".product-name" -->
            <span class="product-price">￥25</span>      <!-- ← Field: ".product-price" -->
            <p class="product-desc">醇厚浓郁</p>         <!-- ← Field: ".product-desc" -->
        </div>
        
        <div class="product-item">  <!-- ← 另一个商品项 -->
            <h3 class="product-name">拿铁咖啡</h3>
            <span class="product-price">￥30</span>
            <p class="product-desc">香滑顺口</p>
        </div>
    </div>
    
    <div class="footer">...</div>
</body>
```

#### ⚙️ **配置示例**

```json
{
    "config": {
        "container": {
            "selector": "body",           // ← 1. 找到整个页面容器
            "by": "css selector"          // ← 新增：定位方式
        },
        "options": {
            "item_selector": ".product-item",  // ← 2. 在body内找到所有商品项
            "item_by": "css selector",         // ← 新增：商品项定位方式
            "wait_timeout": 10,                // ← 新增：元素等待超时
            "implicit_wait": 3                 // ← 新增：隐式等待
        }
    },
    "fields": {
        "name": {
            "selector": ".product-name",   // ← 3. 在每个商品项内提取名称
            "by": "css selector",          // ← 新增：字段定位方式
            "type": "text",
            "wait_visible": true           // ← 新增：等待元素可见
        },
        "price": {
            "selector": ".product-price",  // ← 4. 在每个商品项内提取价格
            "by": "css selector",
            "type": "text",
            "regex": "\\D*([\\d.]+).*"
        },
        "link": {
            "selector": "a",               // ← 5. 提取链接属性
            "by": "css selector",
            "type": "attribute",
            "attribute": "href"
        }
    }
}
```

#### 🎯 **执行过程**

1. **找到Container**: `driver.find_element(By.CSS_SELECTOR, "body")`
2. **找到Items**: `container.find_elements(By.CSS_SELECTOR, ".product-item")` → 找到2个商品项
3. **提取数据**: 对每个商品项执行：
   - `item.find_element(By.CSS_SELECTOR, ".product-name").text` → "美式咖啡"
   - `item.find_element(By.CSS_SELECTOR, ".product-price").text` → "￥25"
   - `item.find_element(By.CSS_SELECTOR, "a").get_attribute("href")` → "https://..."

#### 💡 **为什么这样设计？**

1. **分层定位**: 页面 → 容器 → 商品项 → 字段
2. **灵活性**: 可以适应不同的页面结构
3. **复用性**: 同一个Container下可以有不同类型的Item
4. **精确性**: 避免采集到无关数据
5. **Selenium集成**: 完全兼容 Selenium WebDriver 标准

## 快速开始

### 1. 基本使用

```python
from hybrid_driver.collect import CollectItems

# 创建采集器
collector = CollectItems(config_json=json.dumps(config))

# 执行采集
result = collector.collect(driver)
```

### 2. 配置示例

```python
config = {
    "action": "ACTION_COLLECT_ITEM_INFO",
    "config": {
        "container": {
            "selector": "body",
            "by": "css selector"
        },
        "options": {
            "item_selector": ".product-item",
            "item_by": "css selector",
            "close_dialog": True,
            "max_items": 20,
            "wait_timeout": 10,
            "implicit_wait": 3
        }
    },
    "fields": {
        "name": {
            "selector": ".product-name",
            "by": "css selector",
            "type": "text",
            "required": True,
            "wait_visible": True
        },
        "price": {
            "selector": ".product-price",
            "by": "css selector",
            "type": "text",
            "regex": "\\D*([\\d.]+).*"
        },
        "link": {
            "selector": "a",
            "by": "css selector",
            "type": "attribute",
            "attribute": "href"
        }
    }
}
```

## 配置说明

### 核心配置

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | ✅ | 固定值: "ACTION_COLLECT_ITEM_INFO" |
| `config.container` | object | ✅ | 容器元素配置 |
| `config.options` | object | ✅ | 采集选项配置 |
| `fields` | object | ✅ | 字段定义配置 |

### 容器配置

```json
{
    "container": {
        "selector": "body",
        "by": "css selector",
        "fallback": "html"
    }
}
```

- `selector`: 主容器选择器（通常是页面主区域）
- `by`: **定位方式**（支持 Selenium 标准定位方式）
- `fallback`: 备用容器选择器（可选）

**支持的定位方式**:
- `"css selector"` - CSS选择器（默认）
- `"xpath"` - XPath表达式
- `"id"` - 元素ID
- `"name"` - 元素name属性
- `"class name"` - CSS类名
- `"tag name"` - 标签名
- `"link text"` - 链接文本
- `"partial link text"` - 部分链接文本

**常见Container选择器**:
- `"body"` - 整个页面
- `"#main-content"` - 主要内容区域
- `".product-list"` - 商品列表容器
- `"main"` - 主要内容标签

### 选项配置

```json
{
    "options": {
        "item_selector": ".product-item",
        "item_by": "css selector",
        "close_dialog": true,
        "package": "com.example.app",
        "max_items": 20,
        "scroll_enabled": false,
        "timeout": 30,
        "wait_timeout": 10,
        "implicit_wait": 3,
        "page_load_timeout": 30
    }
}
```

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `item_selector` | string | - | **商品项选择器**（在Container内定位每个商品） |
| `item_by` | string | "css selector" | **商品项定位方式** |
| `close_dialog` | boolean | false | 是否关闭弹窗 |
| `package` | string | - | 应用包名 |
| `max_items` | number | 50 | 最大采集数量 |
| `scroll_enabled` | boolean | true | 是否启用滚动 |
| `timeout` | number | 30 | 采集总超时时间(秒) |
| `wait_timeout` | number | 10 | **元素等待超时时间(秒)** |
| `implicit_wait` | number | 3 | **隐式等待时间(秒)** |
| `page_load_timeout` | number | 30 | **页面加载超时时间(秒)** |

**常见Item选择器**:
- `".product-item"` - 商品项
- `".menu-item"` - 菜单项
- `".card"` - 卡片项
- `".list-item"` - 列表项

### 字段配置

```json
{
    "fields": {
        "name": {
            "selector": ".product-name",
            "by": "css selector",
            "type": "text",
            "required": true,
            "regex": "\\D*([\\d.]+).*",
            "description": "商品名称",
            "attribute": "href",
            "wait_visible": true
        }
    }
}
```

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `selector` | string | ✅ | **字段选择器**（在Item内定位具体数据） |
| `by` | string | "css selector" | **字段定位方式** |
| `type` | string | ✅ | 数据类型(text/attribute/checked/displayed/array) |
| `required` | boolean | false | 是否必填 |
| `regex` | string | false | 正则表达式 |
| `description` | string | false | 字段描述 |
| `attribute` | string | false | **属性名称**（当type为attribute时） |
| `wait_visible` | boolean | false | **是否等待元素可见** |

**支持的数据类型**:
- `"text"` - 元素文本内容（默认）
- `"attribute"` - 元素属性值（需要指定attribute字段）
- `"checked"` - 复选框/单选框选中状态
- `"displayed"` - 元素是否可见
- `"array"` - 数组类型数据

**常见Field选择器**:
- `".product-name"` - 商品名称
- `".product-price"` - 商品价格
- `".product-desc"` - 商品描述
- `".product-image"` - 商品图片
- `"a"` - 链接元素

## Selenium 优化特性

### 1. **标准定位方式支持**

```json
{
    "container": {
        "selector": "//div[@class='product-list']",
        "by": "xpath"
    },
    "fields": {
        "name": {
            "selector": "//h3[@class='product-name']",
            "by": "xpath",
            "type": "text"
        }
    }
}
```

### 2. **智能等待机制**

```json
{
    "options": {
        "wait_timeout": 10,        // 显式等待超时
        "implicit_wait": 3,        // 隐式等待时间
        "page_load_timeout": 30    // 页面加载超时
    },
    "fields": {
        "name": {
            "selector": ".product-name",
            "wait_visible": true    // 等待元素可见
        }
    }
}
```

### 3. **属性提取支持**

```json
{
    "fields": {
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
        }
    }
}
```

### 4. **元素状态检查**

```json
{
    "fields": {
        "is_available": {
            "selector": ".stock-status",
            "type": "displayed"
        },
        "is_selected": {
            "selector": "input[type='checkbox']",
            "type": "checked"
        }
    }
}
```

## 使用示例

### 咖啡菜单采集

```python
from hybrid_driver.collect.examples import coffee_menu_example

config = coffee_menu_example()
collector = CollectItems(config_json=json.dumps(config))
result = collector.collect(driver)
```

### 店铺详情采集

```python
from hybrid_driver.collect.examples import shop_detail_example

config = shop_detail_example()
collector = CollectItems(config_json=json.dumps(config))
result = collector.collect(driver)
```

### 历史订单采集

```python
from hybrid_driver.collect.examples import history_orders_example

config = history_orders_example()
collector = CollectItems(config_json=json.dumps(config))
result = collector.collect(driver)
```

## 测试

### 运行所有测试

```bash
cd hybrid_driver/collect
python examples.py
```

测试包括：
- ✅ 采集器创建测试
- ✅ 旧格式转换测试  
- ✅ HTTP接口测试（需要服务器运行）
  - 咖啡信息收集
  - 配置文件方式
  - 向后兼容性

### HTTP接口测试

当服务器运行时，会自动执行HTTP接口测试：

```bash
# 启动服务器
cd hybrid_driver
python server.py

# 运行测试
cd collect
python examples.py
```

## 向后兼容

### 旧格式参数

```python
# 旧格式
request_data = {
    "serial_id": "device_id",
    "container_selector": "com.example:id/container",
    "item_selectors": {
        "name": "com.example:id/name",
        "price": "com.example:id/price"
    },
    "options": {
        "close_dialog": True,
        "package": "com.example.app"
    }
}

# 自动转换为新格式
config = {
    "action": "ACTION_COLLECT_ITEM_INFO",
    "config": {
        "container": {"selector": "com.example:id/container"},
        "options": {
            "close_dialog": True,
            "package": "com.example.app"
        }
    },
    "fields": {
        "name": {"selector": "com.example:id/name", "type": "text"},
        "price": {"selector": "com.example:id/price", "type": "text"}
    }
}
```

### 旧格式命令转换

```python
from hybrid_driver.collect.examples import convert_legacy_config

# 旧格式命令
legacy_command = """ACTION_COLLECT_ITEM_INFO --close_dialog=1 --pkg=com.example.app --id=com.example:id/container name=com.example:id/name,price=com.example:id/price"""

# 转换为新格式
new_config = convert_legacy_config(legacy_command)
```

## 性能优化

### 缓存配置

```json
{
    "cache": {
        "enabled": true,
        "ttl": 3600,
        "key_pattern": "config_{hash}"
    }
}
```

### 批量处理

```json
{
    "batch": {
        "enabled": true,
        "max_concurrent": 5,
        "timeout": 30
    }
}
```

### 重试机制

```json
{
    "retry": {
        "max_attempts": 3,
        "backoff": "exponential",
        "conditions": ["element_not_found", "timeout"]
    }
}
```

## 错误处理

### 常见错误

| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| `ContainerNotFoundError` | 容器元素未找到 | 检查选择器或添加fallback |
| `ItemNotFoundError` | 商品项未找到 | 检查item_selector配置 |
| `FieldNotFoundError` | 字段元素未找到 | 检查字段选择器 |
| `ValidationError` | 字段验证失败 | 检查required字段和regex |
| `TimeoutError` | 元素等待超时 | 增加wait_timeout或检查网络 |

### 错误处理示例

```python
try:
    result = collector.collect(driver)
except ContainerNotFoundError as e:
    print(f"容器未找到: {e}")
except ItemNotFoundError as e:
    print(f"商品项未找到: {e}")
except FieldNotFoundError as e:
    print(f"字段未找到: {e}")
except ValidationError as e:
    print(f"字段验证失败: {e}")
except TimeoutError as e:
    print(f"等待超时: {e}")
```

## 最佳实践

1. **选择器优化**: 使用稳定的class或id选择器
2. **容器配置**: container使用页面主区域，item_selector使用商品根节点
3. **字段验证**: 为重要字段设置required=true
4. **性能考虑**: 合理设置max_items和timeout
5. **错误处理**: 添加适当的错误处理和重试机制
6. **Selenium优化**: 
   - 使用合适的定位方式（CSS选择器通常最快）
   - 设置合理的等待时间
   - 对重要元素使用wait_visible=true
   - 利用属性提取减少DOM查询

## 迁移指南

### 从旧版本迁移

1. **更新导入**: 使用新的模块路径
2. **配置转换**: 使用convert_legacy_config函数
3. **测试验证**: 运行examples.py验证功能
4. **逐步替换**: 逐步替换旧代码

### 配置文件迁移

```python
# 旧方式
collector = CollectItems(
    container_selector="com.example:id/container",
    item_selectors={"name": "com.example:id/name"}
)

# 新方式
config = {
    "action": "ACTION_COLLECT_ITEM_INFO",
    "config": {
        "container": {"selector": "com.example:id/container"}
    },
    "fields": {
        "name": {"selector": "com.example:id/name", "type": "text"}
    }
}
collector = CollectItems(config_json=json.dumps(config))
```

### Selenium 特定优化

```python
# 优化前
config = {
    "fields": {
        "name": ".product-name",
        "price": ".product-price"
    }
}

# 优化后
config = {
    "options": {
        "wait_timeout": 10,
        "implicit_wait": 3
    },
    "fields": {
        "name": {
            "selector": ".product-name",
            "by": "css selector",
            "type": "text",
            "wait_visible": True
        },
        "price": {
            "selector": ".product-price",
            "by": "css selector",
            "type": "text",
            "regex": "\\D*([\\d.]+).*"
        },
        "link": {
            "selector": "a",
            "by": "css selector",
            "type": "attribute",
            "attribute": "href"
        }
    }
}
``` 