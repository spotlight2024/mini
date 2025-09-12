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
