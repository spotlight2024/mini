import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from hybrid_driver.log_config import get_logger
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils

logger = get_logger(__name__)

class CollectItems:
    """Web端元素信息收集操作 - 对应Native的ACTION_COLLECT_ITEM_INFO"""
    
    def __init__(self, container_selector=None, item_selectors=None, options=None, filters=None, 
                 dialog_views=None, loading_view=None, close_dialog=True, package_name=None,
                 config_json=None, config_file=None):
        # 优先使用新协议配置
        if config_json or config_file:
            self._init_from_json_config(config_json, config_file)
        else:
            # 向后兼容：使用老协议参数
            self._init_from_legacy_params(
                container_selector, item_selectors, options, filters,
                dialog_views, loading_view, close_dialog, package_name
            )

    def _init_from_json_config(self, config_json=None, config_file=None):
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
        
        config_section = config.get('config', {})
        container_config = config_section.get('container', {})
        options_config = config_section.get('options', {})
        filters_config = config_section.get('filters', {})
        fields_config = config.get('fields', {})
        
        # 容器配置
        self.container_selector = container_config.get('selector', '')
        self.fallback_selector = container_config.get('fallback')
        self.container_by = container_config.get('by', 'css selector')  # 新增：定位方式
        
        # 选项配置
        self.close_dialog = options_config.get('close_dialog', True)
        self.package_name = options_config.get('package')
        self.loading_view = options_config.get('loading_view')
        self.dialog_views = options_config.get('dialog_views', [])
        self.dialog_actions = options_config.get('dialog_actions', [])
        self.singleton = options_config.get('singleton', False)
        self.max_items = options_config.get('max_items', 10)
        self.scroll_enabled = options_config.get('scroll_enabled', True)
        self.scroll_direction = options_config.get('scroll_direction', 'down')
        self.timeout = options_config.get('timeout', 30)
        
        # 新增：Selenium 特定配置
        self.wait_timeout = options_config.get('wait_timeout', 10)  # 元素等待超时
        self.implicit_wait = options_config.get('implicit_wait', 3)  # 隐式等待
        self.page_load_timeout = options_config.get('page_load_timeout', 30)  # 页面加载超时
        
        # 商品项配置
        self.item_selector = options_config.get('item_selector')
        self.item_by = options_config.get('item_by', 'css selector')  # 新增：商品项定位方式
        
        # 过滤配置
        self.required_fields = filters_config.get('required_fields', [])
        self.ignore_fields = filters_config.get('ignore_fields', [])
        self.min_items = filters_config.get('min_items', 1)
        
        # 字段配置
        self.item_selectors = self._convert_fields_to_selectors(fields_config)
        
        logger.info(f"Initialized from JSON config: container={self.container_selector} ({self.container_by}), fields={len(self.item_selectors)}")

    def _init_from_legacy_params(self, container_selector, item_selectors, options, filters,
                                dialog_views, loading_view, close_dialog, package_name):
        self.container_selector = container_selector
        self.container_by = 'css selector'  # 默认使用CSS选择器
        self.item_selectors = item_selectors or {}
        self.options = options or {}
        self.filters = filters or {}
        self.dialog_views = dialog_views or []
        self.loading_view = loading_view
        self.close_dialog = close_dialog
        self.package_name = package_name
        self.max_items = self.options.get('max_items', 10)
        self.scroll_enabled = self.options.get('scroll_enabled', True)
        self.scroll_direction = self.options.get('scroll_direction', 'down')
        self.timeout = self.options.get('timeout', 30)
        self.singleton = self.options.get('singleton', False)
        self.required_fields = self.filters.get('required_fields', [])
        self.ignore_fields = self.filters.get('ignore_fields', [])
        self.min_items = self.filters.get('min_items', 1)
        self.dialog_actions = []
        self.wait_timeout = self.options.get('wait_timeout', 10)
        self.implicit_wait = self.options.get('implicit_wait', 3)
        self.page_load_timeout = self.options.get('page_load_timeout', 30)
        self._process_dialog_views()

    def _convert_fields_to_selectors(self, fields_config):
        selectors = {}
        for field_name, field_config in fields_config.items():
            if isinstance(field_config, str):
                selectors[field_name] = {
                    'selector': field_config,
                    'by': 'css selector',
                    'type': 'text',
                    'required': False
                }
            elif isinstance(field_config, dict):
                if field_config.get('type') == 'array':
                    selectors[field_name] = {
                        'type': 'array',
                        'selector': field_config.get('selector'),
                        'by': field_config.get('by', 'css selector'),
                        'fields': self._convert_fields_to_selectors(field_config.get('fields', {}))
                    }
                else:
                    selector_config = {
                        'selector': field_config.get('selector'),
                        'by': field_config.get('by', 'css selector'),
                        'type': field_config.get('type', 'text'),
                        'regex': field_config.get('regex'),
                        'required': field_config.get('required', False),
                        'attribute': field_config.get('attribute'),  # 新增：属性提取
                        'wait_visible': field_config.get('wait_visible', False)  # 新增：等待可见
                    }
                    selectors[field_name] = selector_config
        return selectors

    def _process_dialog_views(self):
        new_dialog_views = []
        new_dialog_actions = []
        for dialog in self.dialog_views:
            if dialog.startswith('click#'):
                new_dialog_actions.append(dialog)
            else:
                new_dialog_views.append(dialog)
        self.dialog_views = new_dialog_views
        self.dialog_actions = new_dialog_actions

    def execute(self, device, context=None):
        logger.info(f"[{self.__class__.__name__}], container={self.container_selector} ({self.container_by}), selectors={self.item_selectors}")
        try:
            # 设置隐式等待
            if hasattr(device, '_driver') and device._driver:
                device._driver.implicitly_wait(self.implicit_wait)
            
            container = self._find_container(device)
            if not container:
                logger.warning(f"Container not found: {self.container_selector}")
                return None
                
            collected_items = []
            start_time = time.time()
            
            while len(collected_items) < self.max_items and (time.time() - start_time) < self.timeout:
                items = self._find_items(container)
                if not items:
                    logger.warning("No items found in container")
                    break
                    
                page_items = self._collect_page_items(device, items)
                collected_items.extend(page_items)
                
                if len(collected_items) >= self.max_items:
                    break
                    
                if self.scroll_enabled and len(page_items) > 0:
                    if not self._scroll_container(device, container):
                        logger.info("No more content to scroll")
                        break
                    time.sleep(1)
                else:
                    break
                    
            filtered_items = self._apply_filters(collected_items)
            if len(filtered_items) < self.min_items:
                logger.warning(f"Collected {len(filtered_items)} items, but minimum required is {self.min_items}")
                return None
                
            if self.singleton and filtered_items:
                result_data = filtered_items[0]
            else:
                result_data = filtered_items
                
            logger.info(f"Successfully collected {len(filtered_items)} items")
            return {
                "items": result_data,
                "total_count": len(filtered_items),
                "collection_time": time.time() - start_time
            }
        except Exception as e:
            logger.error(f"Collection failed: {e}")
            return None

    def _handle_dialog_actions(self, device):
        for action in self.dialog_actions:
            try:
                if action.startswith("click#"):
                    click_selector = action[6:]
                    element = self._wait_for_element(device, "css selector", click_selector, timeout=3)
                    if element:
                        element.click()
                        logger.info(f"Clicked dialog action: {click_selector}")
                        time.sleep(0.5)
            except Exception as e:
                logger.debug(f"Failed to handle dialog action {action}: {e}")

    def _find_container(self, device):
        """使用 Selenium 标准方式查找容器"""
        selectors = self.container_selector.split("||") if self.container_selector else []
        if hasattr(self, 'fallback_selector') and self.fallback_selector:
            selectors.append(self.fallback_selector)
            
        if not selectors or selectors == ['']:
            # 默认使用 body 或 html
            for default_selector in ["body", "html"]:
                try:
                    container = self._wait_for_element(device, "css selector", default_selector, timeout=2)
                    if container:
                        logger.info(f"Using {default_selector} as container")
                        return container
                except Exception:
                    continue
            logger.warning("No container selector provided, and <body>/<html> not found!")
            return None
            
        for selector in selectors:
            try:
                # 使用配置的定位方式
                container = self._wait_for_element(device, self.container_by, selector, timeout=5)
                if container:
                    logger.info(f"Found container with selector: {selector} ({self.container_by})")
                    return container
            except Exception as e:
                logger.debug(f"Container selector failed: {selector}, error: {e}")
                continue
                
        logger.warning(f"No container found with any selector: {selectors}")
        return None

    def _find_items(self, container):
        """使用 Selenium 标准方式查找商品项"""
        if self.item_selector:
            try:
                # 使用配置的定位方式查找商品项
                items = container.find_elements(self.item_by, self.item_selector)
                logger.info(f"Found {len(items)} items with item_selector: {self.item_selector} ({self.item_by})")
                return items
            except Exception as e:
                logger.warning(f"item_selector查找失败: {e}")
                return []
                
        # 如果没有指定item_selector，使用默认方式
        try:
            items = container.find_elements(By.CSS_SELECTOR, "*")
            filtered_items = []
            for item in items:
                try:
                    if item.text.strip() or item.is_displayed():
                        filtered_items.append(item)
                except:
                    continue
            logger.info(f"Fallback查找获得{len(filtered_items)}个子元素")
            return filtered_items
        except Exception as e:
            logger.error(f"Failed to find items: {e}")
            return []

    def _wait_for_element(self, device, by, value, timeout=None):
        """使用 Selenium 标准等待机制"""
        if timeout is None:
            timeout = self.wait_timeout
            
        try:
            if hasattr(device, '_driver') and device._driver:
                return WebDriverUtils.wait_for_element(device._driver, by, value, timeout)
            else:
                # 兼容其他设备类型
                return device.wait_for_element(by, value, timeout)
        except Exception as e:
            logger.debug(f"Wait for element failed: {by}={value}, error: {e}")
            return None

    def _collect_page_items(self, device, items):
        """收集页面商品项数据"""
        page_items = []
        for item in items:
            try:
                item_data = {}
                has_valid_data = False
                
                for field_name, selector_config in self.item_selectors.items():
                    try:
                        if isinstance(selector_config, str):
                            # 向后兼容：字符串格式
                            value = self._extract_value(item, selector_config)
                        elif isinstance(selector_config, dict):
                            if selector_config.get('type') == 'array':
                                value = self._extract_array_value(item, selector_config)
                            else:
                                value = self._extract_complex_value(item, selector_config)
                        else:
                            continue
                            
                        if value is not None:
                            item_data[field_name] = value
                            has_valid_data = True
                    except Exception as e:
                        logger.debug(f"Failed to extract {field_name}: {e}")
                        continue
                        
                if has_valid_data:
                    page_items.append(item_data)
            except Exception as e:
                logger.debug(f"Failed to process item: {e}")
                continue
                
        return page_items

    def _extract_array_value(self, element, array_config):
        """提取数组类型数据"""
        try:
            array_selector = array_config.get('selector', '')
            array_by = array_config.get('by', 'css selector')
            array_fields = array_config.get('fields', {})
            
            array_container = element.find_element(array_by, array_selector)
            if not array_container:
                return None
                
            array_items = array_container.find_elements(By.CSS_SELECTOR, "*")
            array_data = []
            
            for array_item in array_items:
                item_data = {}
                for field_name, field_selector in array_fields.items():
                    try:
                        if isinstance(field_selector, str):
                            value = self._extract_value(array_item, field_selector)
                        elif isinstance(field_selector, dict):
                            value = self._extract_complex_value(array_item, field_selector)
                        else:
                            continue
                            
                        if value is not None:
                            item_data[field_name] = value
                    except Exception as e:
                        logger.debug(f"Failed to extract array field {field_name}: {e}")
                        continue
                        
                if item_data:
                    array_data.append(item_data)
                    
            return array_data
        except Exception as e:
            logger.debug(f"Array extraction failed: {e}")
            return None

    def _extract_complex_value(self, element, selector_config):
        """提取复杂类型数据"""
        selector = selector_config.get('selector', '')
        by = selector_config.get('by', 'css selector')
        value_type = selector_config.get('type', 'text')
        regex_pattern = selector_config.get('regex', '')
        attribute = selector_config.get('attribute')
        wait_visible = selector_config.get('wait_visible', False)
        
        try:
            # 如果需要等待可见
            if wait_visible:
                target = self._wait_for_element_visible(element, by, selector, timeout=3)
            else:
                target = element.find_element(by, selector)
                
            if not target:
                return None
                
            # 根据类型提取值
            if value_type == 'text':
                value = target.text.strip()
            elif value_type == 'attribute' and attribute:
                value = target.get_attribute(attribute)
            elif value_type == 'checked':
                value = target.is_selected()
            elif value_type == 'displayed':
                value = target.is_displayed()
            else:
                value = target.text.strip()
                
            # 应用正则表达式
            if regex_pattern and value:
                import re
                match = re.search(regex_pattern, str(value))
                if match:
                    value = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    
            return value
        except Exception as e:
            logger.debug(f"Complex extraction failed: {e}")
            return None

    def _wait_for_element_visible(self, parent_element, by, selector, timeout=3):
        """等待元素可见"""
        try:
            wait = WebDriverWait(parent_element, timeout)
            return wait.until(EC.visibility_of_element_located((by, selector)))
        except TimeoutException:
            return None

    def _extract_value(self, element, selector):
        """向后兼容的简单值提取"""
        try:
            if "-" in selector:
                return self._extract_composite_value(element, selector)
            target = element.find_element(By.CSS_SELECTOR, selector)
            if target:
                return target.text.strip()
        except:
            pass
        try:
            return element.get_attribute(selector)
        except:
            pass
        return None

    def _extract_composite_value(self, element, composite_selector):
        """提取复合选择器值"""
        parts = composite_selector.split("-")
        if len(parts) >= 2:
            parent_selector = parts[0]
            child_selector = parts[1]
            try:
                parent = element.find_element(By.CSS_SELECTOR, parent_selector)
                if parent:
                    child = parent.find_element(By.CSS_SELECTOR, child_selector)
                    if child:
                        return child.text.strip()
            except:
                pass
        return None

    def _apply_filters(self, items):
        """应用过滤器"""
        filtered_items = []
        for item in items:
            if self.required_fields:
                has_all_required = all(field in item and item[field] for field in self.required_fields)
                if not has_all_required:
                    continue
            if self.ignore_fields:
                for field in self.ignore_fields:
                    item.pop(field, None)
            filtered_items.append(item)
        return filtered_items

    def _handle_dialogs(self, device):
        """处理弹窗"""
        for dialog_selector in self.dialog_views:
            try:
                dialog = self._wait_for_element(device, "css selector", dialog_selector, timeout=3)
                if dialog:
                    close_buttons = dialog.find_elements(By.CSS_SELECTOR, ".close, .btn-close, [data-dismiss='modal']")
                    if close_buttons:
                        close_buttons[0].click()
                        logger.info(f"Closed dialog: {dialog_selector}")
                        time.sleep(0.5)
            except Exception as e:
                logger.debug(f"Failed to handle dialog {dialog_selector}: {e}")

    def _wait_for_loading_complete(self, device):
        """等待加载完成"""
        try:
            start_time = time.time()
            while time.time() - start_time < 10:
                loading = self._wait_for_element(device, "css selector", self.loading_view, timeout=1)
                if not loading:
                    logger.info("Loading completed")
                    break
                time.sleep(0.5)
        except Exception as e:
            logger.debug(f"Loading wait failed: {e}")

    def _scroll_container(self, device, container):
        """滚动容器"""
        try:
            if self.scroll_direction == 'down':
                device.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight", container)
            else:
                device.execute_script("arguments[0].scrollTop = arguments[0].scrollTop - arguments[0].clientHeight", container)
            return True
        except Exception as e:
            logger.debug(f"Scroll failed: {e}")
            return False 