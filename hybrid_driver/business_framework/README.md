# 业务框架 (Business Framework)

## 概述

这是一个基于 `hybrid_driver` 的业务框架，支持多网站、多业务的自动化测试。框架采用分层架构设计，提供高度模块化和可扩展的解决方案。

## 架构设计

### 核心层次

```
┌─────────────────────────────────────────────────────────────┐
│                    Business Layer (业务层)                    │
├─────────────────────────────────────────────────────────────┤
│  TaobaoBusiness  │  JDBusiness  │  OtherSiteBusiness        │
├─────────────────────────────────────────────────────────────┤
│                    Page Layer (页面层)                        │
├─────────────────────────────────────────────────────────────┤
│  TaobaoPages    │  JDPages     │  OtherSitePages           │
├─────────────────────────────────────────────────────────────┤
│                    Action Layer (操作层)                      │
├─────────────────────────────────────────────────────────────┤
│  ActionChains   │  WebDriverChain  │  MultiPageManager      │
├─────────────────────────────────────────────────────────────┤
│                    Core Layer (核心层)                        │
├─────────────────────────────────────────────────────────────┤
│  WebDriverManager  │  ConfigManager  │  LoggerManager       │
└─────────────────────────────────────────────────────────────┘
```

### 目录结构

```
business_framework/
├── core/                           # 核心层
│   ├── webdriver_manager.py       # WebDriver管理
│   ├── page_manager.py            # 页面管理
│   ├── action_chains_wrapper.py   # ActionChains包装器
│   └── webdriver_chain.py         # WebDriver链式调用
├── pages/                          # 页面层
│   ├── base_page.py               # 页面基类
│   └── taobao_pages.py            # 淘宝页面
├── business/                       # 业务层
│   ├── base_business.py           # 业务基类
│   └── taobao_business.py         # 淘宝业务
├── config/                         # 配置层
│   └── sites_config.py            # 网站配置
├── tests/                          # 测试层
│   └── test_taobao_search.py      # 淘宝搜索测试
└── README.md                       # 本文档
```

## 核心特性

### 1. 多页面管理
- 自动跟踪所有打开的页面
- 智能切换页面
- 页面状态管理

### 2. ActionChains支持
- 复杂的鼠标操作
- 键盘操作
- 链式调用

### 3. 链式调用
- 流畅的操作接口
- 易于阅读和维护
- 支持复杂业务流程

### 4. 配置驱动
- 统一的配置管理
- 支持多网站配置
- 易于扩展

### 5. 人类化交互
- 共享的 `HumanMouse` 生成自然轨迹，覆盖 `ActionChainsWrapper` 与 `WebDriverChain`
- 可通过配置或运行时开关启停，参数包括步数、延迟、抖动、过冲概率等
- 剩余功能保持向后兼容，关掉开关后回退到原生 Selenium 行为
- 日志记录耗时、路径长度与过冲等指标，便于调优

## 使用示例

### 基本使用

```python
from business_framework.business.taobao_business import TaobaoBusiness

# 创建淘宝业务实例
taobao_business = TaobaoBusiness(session_id=1)

try:
    # 初始化
    taobao_business.initialize()
    taobao_business.initialize_pages()
    
    # 执行业务
    success = taobao_business.execute_business_flow()
    
    if success:
        print("✅ 业务执行成功")
    else:
        print("❌ 业务执行失败")
        
finally:
    # 清理资源
    taobao_business.cleanup()
```

### 使用ActionChains

```python
# 使用ActionChains执行复杂操作
success = taobao_business.execute_image_search_with_actions("logo.png")
```

### 并发测试

```python
from business_framework.tests.test_taobao_search import test_taobao_concurrent_with_actions

# 执行并发测试
test_taobao_concurrent_with_actions(concurrent_count=2)
```

## 人类化交互使用指南

### 原理概述

- `core/human_actions.py` 定义 `HumanMouse`，根据配置生成多段 `pointerMove` / `pointerDown` / `pointerUp`，融入曲线、抖动与可选过冲；
- `BaseBusiness.initialize()` 会根据站点配置创建一次 `HumanMouse` 并注入 `ActionChainsWrapper` 与 `WebDriverChain`，从而让链式 API 无缝支持人类化行为；
- 当开关关闭时自动退回原生 Selenium 操作；启用时同一实例保持上次指针位置形成连续轨迹；
- 每次动作完成会输出 `[HumanMouse] action=... duration=... path=... overshoot=...` 以及 `[ActionChains] perform human=... ops=... elapsed=...` 等日志。

### 如何开启/关闭

1. **调用层（FastAPI Taobao 示例）**
   ```json
   {
     "uid": "tester001",
     "human_actions": {
       "min_steps": 16,
       "max_steps": 28,
       "min_step_duration_ms": 20,
       "max_step_duration_ms": 45,
       "overshoot_chance": 0.3
     }
   }
   ```
   - 只要提供 `human_actions` 字段即视为开启人类化行为；
   - 未填写的子参数使用框架默认值。

2. **站点配置层（自定义业务）**
   ```python
   site_config = {
       "site_name": "demo",
       # ... 其它浏览器选项 ...
       "human_actions": {
           "min_steps": 12,
           "max_steps": 24,
           "path_jitter": 0.8,
           "overshoot_chance": 0.2
       }
   }
  ```

3. **运行时切换**
   ```python
   actions = business.get_action_chains()
   actions.disable_human_actions()  # 临时关闭
   actions.enable_human_actions()   # 再次开启
   ```

### 主要参数一览

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `enabled` | 是否启用人类化行为（框架自动设置，调用方无需填写） | `False` |
| `min_steps` / `max_steps` | 轨迹分段数量范围 | `10` / `24` |
| `min_step_duration_ms` / `max_step_duration_ms` | 每段移动耗时 | `12` / `36` |
| `min_pause` / `max_pause` | 段间随机停顿（秒） | `0.01` / `0.05` |
| `path_jitter` | 单段轨迹抖动幅度（像素） | `0.7` |
| `target_jitter` | 落点偏移（像素） | `2.5` |
| `overshoot_chance` | 过冲概率 | `0.2` |
| `overshoot_range` | 过冲距离范围（像素） | `(1.5, 4.0)` |
| `seed` | 随机种子（固定轨迹） | `None` |

### 配置建议与场景

- `min_steps` / `max_steps`：小于 12 会让轨迹略显生硬；常规用户推荐 14~26，若目标站风控严格可提高 `max_steps`；长路径时也要结合页面响应时间。  
- `min_step_duration_ms` / `max_step_duration_ms`：决定移动速度。快速场景（需兼顾效率）可维持 12/36；仿真人慢速可拉到 25/60。避免过低（<10ms）导致动作过于机械。  
- `min_pause` / `max_pause`：用于两个 pointerMove 之间的停顿。若需模拟“犹豫”可增大到 0.05~0.12；若强调效率可降到 0.005~0.02。  
- `path_jitter`：轨迹噪声，0.5~1.2 比较自然；太大可能偏离元素，尤其在小按钮上需慎用。  
- `target_jitter`：控制点击落点分布。对大按钮可保持 2~4 像素；对精确控件（复选框、输入框图标）建议 <=1。  
- `overshoot_chance` 与 `overshoot_range`：模拟过冲回拉。若站点监控鼠标抖动，可保留 0.1~0.3；若页面元素靠近边界或易触发误点，可降为 0。  
- `seed`：用于重放测试或稳定集成环境；线上常置 `None` 以获得更多随机性。  
- 如果只想快速开启默认人类化，直接传空字典 `"human_actions": {}` 即可；需完全关闭则省略该字段。

### 日志排查建议

- 关注 `[HumanMouse]` 日志可查看每次行为耗时、路径长度、是否过冲；
- `[ActionChains] perform ...` 汇总本次链路步骤，用于快速对照；
- 将日志级别调到 `DEBUG` 可看到每一步的排队记录（`queued move(...)`、`queued click(...)`）；
- 若不希望过冲，将 `overshoot_chance` 设为 `0`；若需要更短动作，可降低 `max_steps` 或缩短 `min_step_duration_ms`。

## 扩展指南

### 添加新网站

1. **创建页面类**
```python
# pages/new_site_pages.py
class NewSiteHomePage(BasePage):
    def __init__(self, driver, page_manager, site_config, session_id):
        super().__init__(driver, page_manager, site_config, session_id)
        # 定义页面元素
        self.locators = {
            'search_button': (By.CLASS_NAME, "search-btn"),
            # 更多元素...
        }
    
    def is_loaded(self):
        # 实现页面加载检查
        pass
```

2. **创建业务类**
```python
# business/new_site_business.py
class NewSiteBusiness(BaseBusiness):
    def __init__(self, session_id):
        site_config = SitesConfig.get_site_config('new_site')
        super().__init__(site_config, session_id)
    
    def execute_business_flow(self):
        # 实现业务逻辑
        pass
```

3. **添加配置**
```python
# config/sites_config.py
NEW_SITE = {
    'site_name': 'new_site',
    'home_url': 'https://www.newsite.com/',
    'hub_url': 'http://172.16.1.129:30444/wd/hub',
    # 更多配置...
}
```

### 添加新业务

1. **继承业务基类**
2. **实现业务逻辑**
3. **添加测试用例**

## 与jd_test_actions.py的对比

| 特性 | jd_test_actions.py | 新框架 |
|------|-------------------|--------|
| 架构 | 单一文件 | 分层架构 |
| 扩展性 | 难以扩展 | 高度可扩展 |
| 复用性 | 代码重复 | 高度复用 |
| 维护性 | 难以维护 | 易于维护 |
| 测试性 | 难以测试 | 易于测试 |
| 配置管理 | 硬编码 | 配置驱动 |

## 优势

1. **高度模块化** - 每个层次职责清晰
2. **易于扩展** - 新网站、新业务可以快速添加
3. **代码复用** - 通用功能可以共享
4. **配置驱动** - 通过配置文件管理不同网站
5. **错误处理** - 完善的异常处理机制
6. **日志管理** - 统一的日志记录
7. **多页面支持** - 自动处理页面切换
8. **ActionChains支持** - 处理复杂交互

## 运行测试

```bash
# 运行淘宝搜索测试
cd hybrid_driver/business_framework
python tests/test_taobao_search.py
```

## 总结

这个业务框架提供了一个完整的多网站、多业务自动化测试解决方案。它基于 `hybrid_driver` 构建，充分利用了现有的基础设施，同时提供了更好的架构设计和扩展性。

通过这个框架，您可以：
- 快速开发新的业务逻辑
- 轻松支持新的网站
- 复用通用的操作和页面逻辑
- 进行并发测试
- 管理复杂的多页面交互
