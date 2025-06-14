# 操作指令说明文档

## 基础操作指令

### Click 点击操作

用于执行元素点击操作，支持等待新窗口和页面渲染。

#### 参数定义

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| type | string | 是 | - | 固定值 "click" |
| method | string | 是 | - | 元素定位方法，如 "css selector" |
| selector | string | 是 | - | 元素选择器 |
| timeout | integer | 否 | 10 | 超时时间（秒） |
| wait_for_new_window | boolean | 否 | false | 是否等待新窗口打开 |
| wait_for_render | boolean | 否 | true | 是否等待页面渲染完成 |

#### 使用示例

1. 基本点击操作（只等待页面渲染）
```json
{
    "type": "click",
    "method": "css selector",
    "selector": "#button",
    "timeout": 10
}
```

2. 点击并等待新窗口
```json
{
    "type": "click",
    "method": "css selector",
    "selector": "#button",
    "timeout": 10,
    "wait_for_new_window": true
}
```

3. 点击但不等待页面渲染
```json
{
    "type": "click",
    "method": "css selector",
    "selector": "#button",
    "timeout": 10,
    "wait_for_render": false
}
```

### WaitForNewWindow 等待新窗口

用于等待新窗口打开并自动切换到新窗口。

#### 参数定义

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| type | string | 是 | - | 固定值 "wait_for_new_window" |
| timeout | integer | 否 | 10 | 超时时间（秒） |

#### 使用示例

```json
{
    "type": "wait_for_new_window",
    "timeout": 10
}
```

### WaitForPageRender 等待页面渲染

用于等待页面完全渲染完成。

#### 参数定义

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| type | string | 是 | - | 固定值 "wait_for_page_render" |
| timeout | integer | 否 | 10 | 超时时间（秒） |

#### 使用示例

```json
{
    "type": "wait_for_page_render",
    "timeout": 10
}
```

## 条件判断指令

### If 条件判断

用于根据条件执行不同的操作序列。

#### 参数定义

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| type | string | 是 | - | 固定值 "if" |
| condition_op | object | 是 | - | 条件操作对象 |
| then_op | object | 是 | - | 条件为真时执行的操作 |
| else_op | object | 否 | null | 条件为假时执行的操作 |

#### 使用示例

1. 基本条件判断
```json
{
    "type": "if",
    "condition_op": {
        "type": "find",
        "method": "css selector",
        "selector": "#button"
    },
    "then_op": {
        "type": "click",
        "method": "css selector",
        "selector": "#button"
    }
}
```

2. 带 else 分支的条件判断
```json
{
    "type": "if",
    "condition_op": {
        "type": "find",
        "method": "css selector",
        "selector": "#button"
    },
    "then_op": {
        "type": "click",
        "method": "css selector",
        "selector": "#button"
    },
    "else_op": {
        "type": "click",
        "method": "css selector",
        "selector": "#alternative-button"
    }
}
```

3. 嵌套条件判断
```json
{
    "type": "if",
    "condition_op": {
        "type": "find",
        "method": "css selector",
        "selector": "#button"
    },
    "then_op": {
        "type": "if",
        "condition_op": {
            "type": "find",
            "method": "css selector",
            "selector": "#sub-button"
        },
        "then_op": {
            "type": "click",
            "method": "css selector",
            "selector": "#sub-button"
        }
    }
}
```

### Sequence 序列操作

用于按顺序执行多个操作。

#### 参数定义

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| type | string | 是 | - | 固定值 "sequence" |
| operations | array | 是 | - | 操作对象数组 |

#### 使用示例

```json
{
    "type": "sequence",
    "operations": [
        {
            "type": "click",
            "method": "css selector",
            "selector": "#button1"
        },
        {
            "type": "click",
            "method": "css selector",
            "selector": "#button2"
        }
    ]
}
```

## 使用建议

1. 对于普通的点击操作，使用默认配置即可（`wait_for_render=true`）
2. 对于会打开新窗口的点击操作，设置 `wait_for_new_window=true`
3. 如果点击后需要立即执行其他操作，可以设置 `wait_for_render=false`
4. 可以根据需要调整 `timeout` 参数
5. 所有操作都支持通过 `trace_id` 进行日志追踪

## 注意事项

1. 超时时间（timeout）建议根据实际网络环境和页面复杂度来设置
2. 等待新窗口操作会自动切换到新打开的窗口
3. 等待页面渲染操作会检查 document.readyState 状态
4. 所有操作都有详细的日志记录，方便问题排查
5. 操作失败时会返回 false 或抛出异常，请做好错误处理
6. 条件判断操作支持嵌套使用，但要注意控制嵌套层级，避免过于复杂
7. 序列操作中的操作会按顺序执行，如果某个操作失败，后续操作仍会继续执行