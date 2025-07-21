#!/usr/bin/env python3
"""
Web端元素信息收集 - 版本2
重点解决数据关联性问题，确保同一item下的字段数据正确关联
"""

import time
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from hybrid_driver.log_config import get_logger
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils

logger = get_logger(__name__)


class CollectItemsV2:
    """Web端元素信息收集操作 - 版本2，解决数据关联性问题"""
    
    def __init__(self, config_json=None, config_file=None, **kwargs):
        # 优先使用新协议配置
        if config_json or config_file:
            self._init_from_json_config(config_json, config_file)
        else:
            # 向后兼容：使用老协议参数
            self._init_from_legacy_params(**kwargs)

    def _init_from_json_config(self, config_json=None, config_file=None):
        """从JSON配置初始化"""
        config = {}
        if config_file:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file {config_file}: {e}")
                raise
        elif config_json:
            try:
                config = json.loads(config_json)
            except Exception as e:
                logger.error(f"Failed to parse config JSON: {e}")
                raise
        
        # 解析配置
        config_section = config.get('config', {})
        self.container_config = config_section.get('container', {})
        self.item_config = config_section.get('item', {})
        self.options_config = config_section.get('options', {})
        self.filters_config = config_section.get('filters', {})
        self.fields_config = config.get('fields', {})
        
        # 设置默认值
        self._set_defaults()
        
        logger.info(f"Initialized from JSON config: container={self.container_config.get('selector')}, item={self.item_config.get('selector')}, fields={len(self.fields_config)}")

    def _init_from_legacy_params(self, **kwargs):
        """从老协议参数初始化"""
        self.container_config = {
            'selector': kwargs.get('container_selector', 'body'),
            'by': 'css selector'
        }
        self.item_config = {
            'selector': kwargs.get('item_selector', '*'),
            'by': 'css selector',
            'required': False
        }
        self.options_config = {
            'close_dialog': kwargs.get('close_dialog', True),
            'package': kwargs.get('package_name', ''),
            'loading_view': kwargs.get('loading_view', ''),
            'singleton': kwargs.get('singleton', False),
            'max_items': kwargs.get('max_items', 10),
            'scroll_enabled': kwargs.get('scroll_enabled', True),
            'scroll_direction': 'down' if not kwargs.get('reverse') else 'up',
            'timeout': kwargs.get('timeout', 30),
            'wait_timeout': kwargs.get('wait_timeout', 10),
            'implicit_wait': kwargs.get('implicit_wait', 3),
            'page_load_timeout': kwargs.get('page_load_timeout', 30)
        }
        self.filters_config = {
            'required_fields': kwargs.get('required_fields', []),
            'ignore_fields': kwargs.get('ignore_fields', []),
            'min_items': kwargs.get('min_items', 1)
        }
        
        # 转换字段配置
        self.fields_config = {}
        item_selectors = kwargs.get('item_selectors', {})
        for field_name, selector in item_selectors.items():
            self.fields_config[field_name] = {
                'selector': selector,
                'type': 'text',
                'required': False
            }
        
        self._set_defaults()

    def _set_defaults(self):
        """设置默认值"""
        # 容器默认值
        if 'by' not in self.container_config:
            self.container_config['by'] = 'css selector'
        
        # 项目默认值
        if 'by' not in self.item_config:
            self.item_config['by'] = 'css selector'
        if 'required' not in self.item_config:
            self.item_config['required'] = True
        
        # 选项默认值
        defaults = {
            'close_dialog': True,
            'package': '',
            'loading_view': '',
            'singleton': False,
            'max_items': 10,
            'scroll_enabled': True,
            'scroll_direction': 'down',
            'timeout': 30,
            'wait_timeout': 10,
            'implicit_wait': 3,
            'page_load_timeout': 30
        }
        for key, default_value in defaults.items():
            if key not in self.options_config:
                self.options_config[key] = default_value
        
        # 过滤器默认值
        filter_defaults = {
            'required_fields': [],
            'ignore_fields': [],
            'min_items': 1
        }
        for key, default_value in filter_defaults.items():
            if key not in self.filters_config:
                self.filters_config[key] = default_value

    def execute(self, device, context=None):
        """执行收集操作"""
        logger.info(f"[{self.__class__.__name__}] 开始收集: container={self.container_config.get('selector')}, item={self.item_config.get('selector')}")
        
        try:
            # 设置隐式等待
            if hasattr(device, '_driver') and device._driver:
                device._driver.implicitly_wait(self.options_config['implicit_wait'])
            
            # 1. 找到容器
            container = self._find_container(device)
            if not container:
                logger.warning(f"Container not found: {self.container_config.get('selector')}")
                return self._create_error_response(1004, "Container not found")
            
            # 2. 收集数据
            collected_items = []
            start_time = time.time()
            
            while len(collected_items) < self.options_config['max_items'] and (time.time() - start_time) < self.options_config['timeout']:
                # 找到当前页面的所有项目
                items = self._find_items(container)
                if not items:
                    logger.warning("No items found in container")
                    break
                
                # 收集当前页面的项目数据
                page_items = self._collect_page_items(device, items)
                collected_items.extend(page_items)
                
                if len(collected_items) >= self.options_config['max_items']:
                    break
                
                # 滚动加载更多
                if self.options_config['scroll_enabled'] and len(page_items) > 0:
                    if not self._scroll_container(device, container):
                        logger.info("No more content to scroll")
                        break
                    time.sleep(1)
                else:
                    break
            
            # 3. 应用过滤器
            filtered_items = self._apply_filters(collected_items)
            if len(filtered_items) < self.filters_config['min_items']:
                logger.warning(f"Collected {len(filtered_items)} items, but minimum required is {self.filters_config['min_items']}")
                return self._create_error_response(1003, "Not enough items collected")
            
            # 4. 格式化结果
            if self.options_config['singleton'] and filtered_items:
                result_data = filtered_items[0]
            else:
                result_data = filtered_items
            
            collection_time = time.time() - start_time
            logger.info(f"Successfully collected {len(filtered_items)} items in {collection_time:.2f}s")
            
            return {
                "code": 0,
                "message": "收集成功",
                "data": {
                    "items": result_data,
                    "total_count": len(filtered_items),
                    "collection_time": collection_time
                }
            }
            
        except Exception as e:
            logger.error(f"Collection failed: {e}")
            return self._create_error_response(2000, f"System error: {str(e)}")

    def _find_container(self, device):
        """找到容器元素"""
        selector = self.container_config.get('selector', 'body')
        by = self.container_config.get('by', 'css selector')
        fallback = self.container_config.get('fallback')
        
        # 尝试主选择器
        try:
            container = self._wait_for_element(device, by, selector, timeout=5)
            if container:
                logger.info(f"Found container with selector: {selector} ({by})")
                return container
        except Exception as e:
            logger.debug(f"Container selector failed: {selector}, error: {e}")
        
        # 尝试备选选择器
        if fallback:
            try:
                container = self._wait_for_element(device, by, fallback, timeout=3)
                if container:
                    logger.info(f"Found container with fallback selector: {fallback}")
                    return container
            except Exception as e:
                logger.debug(f"Fallback selector failed: {fallback}, error: {e}")
        
        # 尝试默认选择器
        for default_selector in ["body", "html"]:
            try:
                container = self._wait_for_element(device, "css selector", default_selector, timeout=2)
                if container:
                    logger.info(f"Using {default_selector} as container")
                    return container
            except Exception:
                continue
        
        return None

    def _find_items(self, container):
        """在容器内找到所有项目元素"""
        selector = self.item_config.get('selector', '*')
        by = self.item_config.get('by', 'css selector')
        
        try:
            items = container.find_elements(self._get_by_type(by), selector)
            logger.info(f"Found {len(items)} items with selector: {selector} ({by})")
            return items
        except Exception as e:
            logger.error(f"Failed to find items: {e}")
            return []

    def _collect_page_items(self, device, items):
        """收集页面项目数据 - 关键方法，确保数据关联性"""
        page_items = []
        
        for item_index, item in enumerate(items):
            try:
                item_data = {}
                has_valid_data = False
                
                # 对每个项目，收集所有字段数据
                for field_name, field_config in self.fields_config.items():
                    try:
                        value = self._extract_field_value(item, field_config)
                        if value is not None:
                            item_data[field_name] = value
                            has_valid_data = True
                    except Exception as e:
                        logger.debug(f"Failed to extract {field_name} from item {item_index}: {e}")
                        continue
                
                if has_valid_data:
                    page_items.append(item_data)
                    logger.debug(f"Collected item {item_index}: {item_data}")
                else:
                    logger.debug(f"Item {item_index} has no valid data")
                    
            except Exception as e:
                logger.debug(f"Failed to process item {item_index}: {e}")
                continue
        
        logger.info(f"Collected {len(page_items)} valid items from current page")
        return page_items

    def _extract_field_value(self, item_element, field_config):
        """从项目元素中提取字段值"""
        selector = field_config.get('selector', '')
        field_type = field_config.get('type', 'text')
        regex_pattern = field_config.get('regex')
        attribute_name = field_config.get('attribute', '')
        
        try:
            # 查找字段元素
            target_element = item_element.find_element(By.CSS_SELECTOR, selector)
            if not target_element:
                return None
            
            # 根据类型提取值
            if field_type == 'text':
                value = target_element.text.strip()
            elif field_type == 'attribute':
                value = target_element.get_attribute(attribute_name)
            elif field_type == 'checked':
                value = str(target_element.is_selected()).lower()
            else:
                value = target_element.text.strip()
            
            # 应用正则表达式
            if regex_pattern and value:
                match = re.search(regex_pattern, value)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
            
            return value if value else None
            
        except Exception as e:
            logger.debug(f"Failed to extract field value: {e}")
            return None

    def _scroll_container(self, device, container):
        """滚动容器"""
        try:
            # 使用JavaScript滚动
            if self.options_config['scroll_direction'] == 'up':
                device._driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop - 500", container)
            else:
                device._driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + 500", container)
            
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.debug(f"Scroll failed: {e}")
            return False

    def _apply_filters(self, items):
        """应用过滤器"""
        filtered_items = []
        required_fields = self.filters_config.get('required_fields', [])
        ignore_fields = self.filters_config.get('ignore_fields', [])
        
        for item in items:
            # 检查必需字段
            if required_fields:
                has_all_required = all(field in item and item[field] for field in required_fields)
                if not has_all_required:
                    continue
            
            # 移除忽略字段
            if ignore_fields:
                for field in ignore_fields:
                    item.pop(field, None)
            
            filtered_items.append(item)
        
        return filtered_items

    def _wait_for_element(self, device, by, value, timeout=None):
        """等待元素出现"""
        if timeout is None:
            timeout = self.options_config['wait_timeout']
        
        try:
            if hasattr(device, '_driver') and device._driver:
                return WebDriverUtils.wait_for_element(device._driver, by, value, timeout)
            else:
                return device.wait_for_element(by, value, timeout)
        except Exception as e:
            logger.debug(f"Wait for element failed: {by}={value}, error: {e}")
            return None

    def _get_by_type(self, by_string):
        """转换定位方式字符串为By类型"""
        by_map = {
            'css selector': By.CSS_SELECTOR,
            'xpath': By.XPATH,
            'id': By.ID,
            'name': By.NAME,
            'class name': By.CLASS_NAME,
            'tag name': By.TAG_NAME,
            'link text': By.LINK_TEXT,
            'partial link text': By.PARTIAL_LINK_TEXT
        }
        return by_map.get(by_string.lower(), By.CSS_SELECTOR)

    def _create_error_response(self, code, message):
        """创建错误响应"""
        return {
            "code": code,
            "message": message,
            "error": message
        }


# 向后兼容的工厂函数
def create_collector(config_json=None, config_file=None, **kwargs):
    """创建收集器实例"""
    return CollectItemsV2(config_json=config_json, config_file=config_file, **kwargs) 