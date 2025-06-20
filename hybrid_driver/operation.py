import time
from abc import ABC, abstractmethod
from hybrid_driver.log_config import get_logger
from hybrid_driver.webdriver.webdriver_utils import WebDriverUtils

logger = get_logger(__name__)

class OperationRegistry:
    _registry = {}

    @classmethod
    def register(cls, name):
        def decorator(op_cls):
            cls._registry[name] = op_cls
            return op_cls
        return decorator

    @classmethod
    def get(cls, name):
        return cls._registry.get(name)

    @classmethod
    def all(cls):
        return dict(cls._registry)

class Operation(ABC):
    @abstractmethod
    def execute(self, device, context=None):
        pass

# ================= 基础指令 =================

@OperationRegistry.register("find")
class FindElement(Operation):
    def __init__(self, method, selector, timeout=10):
        self.method = method
        self.selector = selector
        self.timeout = timeout

    def execute(self, device, context=None):
        logger.info(f"[{FindElement}], method={self.method}, selector={self.selector}, timeout={self.timeout}")
        try:
            # 如果上下文中已有元素，且选择器匹配，则直接返回
            if context and 'element' in context:
                element = context['element']
                if self._element_matches(element):
                    logger.info(f"[{FindElement}], Using cached element: {self.selector}")
                    return element

            # 查找元素
            elem = device.wait_for_element(self.method, self.selector, self.timeout)
            if elem:
                logger.info(f"[{FindElement}], Element found: {elem}")
                # 更新上下文
                if context:
                    context['element'] = elem
                return elem
            else:
                logger.warning(f"[{FindElement}], Element not found: {self.selector}")
                return None
        except Exception as e:
            logger.error(f"Exception: {e}")
            return None

    def _element_matches(self, element):
        """检查元素是否匹配当前选择器"""
        try:
            if self.method == "css selector":
                return element.get_attribute("css") == self.selector
            elif self.method == "xpath":
                return element.get_attribute("xpath") == self.selector
            elif self.method == "id":
                return element.get_attribute("id") == self.selector
            return False
        except:
            return False

@OperationRegistry.register("click")
class Click(Operation):
    def __init__(self, wait_for_new_window=False, timeout=10, method=None, selector=None,native_action=None, context_type="WEB"):
        self.native_action = native_action
        self.wait_for_new_window = wait_for_new_window
        self.timeout = timeout
        self.method = method
        self.selector = selector
        self.context_type = context_type.upper()  # 统一转为大写

    def execute(self, device, context=None):
        logger.info(f"[{Click}], wait_for_new_window={self.wait_for_new_window}, timeout={self.timeout}, method={self.method}, selector={self.selector}, context_type={self.context_type}")
        try:
            # 获取要点击的元素
            element = context.get('element') if context else None

            # 根据context_type执行不同的点击逻辑
            if self.context_type == "WEB":
                self._execute_web_click(device, element, context)
            elif self.context_type == "NATIVE":
                self._execute_native_click(device, self.native_action, context)
            else:
                logger.error(f"[{Click}], Unsupported context_type: {self.context_type}")

            # 如果需要等待新窗口
            if self.wait_for_new_window:
                # 1. 先切换到对应的 page  2.等待 page 渲染
                device.switch_to_new_window()
                device.wait_for_page_load()
            return True
        except Exception as e:
            logger.error(f"Exception: {e}")
            return False

    def _execute_web_click(self, device, element, context):
        """执行WEB类型的点击操作"""
        logger.info(f"[{Click}], Executing WEB click")
        # 如果提供了method和selector，先查找元素
        if self.method and self.selector:
            logger.info(f"[{Click}], Finding element with method={self.method}, selector={self.selector}")
            find_op = FindElement(self.method, self.selector, self.timeout)
            element = find_op.execute(device, context)
            if not element:
                logger.error(f"[{Click}], Element not found with method={self.method}, selector={self.selector}")
                return False
        try:
            # 如果需要等待新窗口，先获取当前窗口句柄
            if self.wait_for_new_window:
                old_handles = set(device.get_window_handles())

            # 执行点击
            element.click()
            logger.info("Element clicked successfully")
            return True
        except Exception as e:
            logger.error(f"WEB click failed: {e}")
            return False

    def _execute_native_click(self, device, native_action, context):
        """执行NATIVE类型的点击操作"""
        logger.info(f"[{Click}], Executing NATIVE click")
        try:
            cmd = f'am broadcast -a ai.guangfan.execution.ACTION_EXECUTE_COMMAND -n ai.guangfan.assistant/ai.guangfan.execution.AdbCommandReceiver --es command "{native_action}"'
            logger.info(f"NATIVE click : action : {cmd}")
            device.get_adb_device().shell(cmd)
            # 临时返回成功，等待后续实现
            return True
        except Exception as e:
            logger.error(f"NATIVE click failed: {e}")
            return False

@OperationRegistry.register("wait")
class Wait(Operation):
    def __init__(self, seconds):
        self.seconds = seconds

    def execute(self, device, trace_id=None, context=None):
        logger.info(f"trace_id={trace_id}, seconds={self.seconds}")
        time.sleep(self.seconds)
        return True

@OperationRegistry.register("js")
class JS(Operation):
    def __init__(self, script):
        self.script = script

    def execute(self, device, context=None):
        logger.info(f"script={self.script}")
        try:
            result = device.execute_script(self.script)
            logger.info(f"Script executed, result: {result}")
            return result
        except Exception as e:
            logger.error(f"Exception: {e}")
            return None

@OperationRegistry.register("handle_popup")
class HandlePopup(Operation):
    def __init__(self, popup_selector, timeout=3):
        self.popup_selector = popup_selector
        self.timeout = timeout

    def execute(self, device, context=None):
        logger.info(f"selector={self.popup_selector}, timeout={self.timeout}")
        try:
            popup = device.wait_for_element("css selector", self.popup_selector, self.timeout)
            if popup:
                popup.click()
                logger.info(f"Popup closed: {self.popup_selector}")
                return True
        except Exception as e:
            logger.warning(f"Exception: {e}")
        return False

@OperationRegistry.register("input")
class Input(Operation):
    def __init__(self, text, timeout=10):
        self.text = text
        self.timeout = timeout

    def execute(self, device, context=None):
        logger.info(f"text={self.text}, timeout={self.timeout}")
        try:
            # 获取要输入的元素
            element = context.get('element') if context else None
            if not element:
                logger.error("No element to input")
                return False

            # 执行输入
            element.clear()
            element.send_keys(self.text)
            logger.info(f"Input text '{self.text}' successfully")
            return True
        except Exception as e:
            logger.error(f"Exception: {e}")
            return False

@OperationRegistry.register("assert_text")
class AssertText(Operation):
    def __init__(self, method, selector, expected, timeout=10):
        self.method = method
        self.selector = selector
        self.expected = expected
        self.timeout = timeout

    def execute(self, device, trace_id=None, context=None):
        logger.info(f"trace_id={trace_id}, method={self.method}, selector={self.selector}, expected={self.expected}")
        try:
            elem = device.wait_for_element(self.method, self.selector, self.timeout, trace_id=trace_id)
            if elem and self.expected in elem.text:
                logger.info(f"Assertion passed: '{self.expected}' in '{elem.text}'")
                return True
            else:
                msg = f"Assertion failed: '{self.expected}' not in '{elem.text if elem else None}'"
                logger.warning(msg)
                raise AssertionError(msg)
        except Exception as e:
            logger.error(f"Exception: {e}")
            raise

# ================= 复合指令 =================

@OperationRegistry.register("sequence")
class Sequence(Operation):
    def __init__(self, operations):
        self.operations = operations

    def execute(self, device, trace_id=None, context=None):
        logger.info(f"trace_id={trace_id}, steps={len(self.operations)}")
        results = []
        for idx, op in enumerate(self.operations):
            try:
                result = op.execute(device, trace_id=trace_id, context=context)
                results.append(result)
            except Exception as e:
                logger.error(f"Step {idx+1} ({op.__class__.__name__}) failed: {e}")
                results.append(None)
        return results

@OperationRegistry.register("if")
class If(Operation):
    def __init__(self, condition_op, then_op, else_op=None):
        self.condition_op = condition_op
        self.then_op = then_op
        self.else_op = else_op

    def execute(self, device, trace_id=None, context=None):
        logger.info(f"trace_id={trace_id}, evaluating condition...")
        try:
            cond = self.condition_op.execute(device, trace_id=trace_id, context=context)
            if cond:
                logger.info("Condition true, executing then_op")
                return self.then_op.execute(device, trace_id=trace_id, context=context)
            elif self.else_op:
                logger.info("Condition false, executing else_op")
                return self.else_op.execute(device, trace_id=trace_id, context=context)
            else:
                logger.info("Condition false, no else_op")
                return None
        except Exception as e:
            logger.error(f"Exception: {e}")
            return None

# ================= 指令流运行器 =================

class OperationSequence:
    def __init__(self, operations):
        self.operations = operations

    def execute(self, device):
        """
        执行操作序列
        :param device: 设备实例
        :return: 执行结果列表
        """
        results = []
        context = {}  # 创建上下文对象

        for idx, op in enumerate(self.operations):
            # 前置钩子：自动处理弹窗
            # try:
            #     device.handle_common_popups()
            # except Exception as e:
            #     logger.warning(f"handle_common_popups failed: {e}")

            start = time.time()
            try:
                # 如果是OperationItem，先构建操作实例
                if isinstance(op, OperationItem):
                    op = op.build()
                
                # 执行操作并传递上下文
                result = op.execute(device, context=context)
                
                # 如果结果是元素，存储到上下文中
                if hasattr(result, 'tag_name'):  # 检查是否是WebElement
                    context['element'] = result
                
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
                logger.error(f"Step {idx+1} ({op.__class__.__name__}) failed: {e}")

            elapsed = time.time() - start
            results.append({
                "step": idx + 1,
                "action": op.__class__.__name__,
                "success": success,
                "result": str(result),
                "error": error,
                "elapsed": elapsed
            })

            # 如果操作失败且不是最后一个操作，可以选择是否继续
            if not success and idx < len(self.operations) - 1:
                logger.warning("Operation failed, but continuing with next operation")

        return results

# ================= 指令流构建器 =================
def build_operations(op_dicts):
    """
    根据指令流配置（dict 列表）递归构建指令对象列表。
    支持复合指令（如 sequence、if）递归构建。
    """
    ops = []
    for op in op_dicts:
        op_type = op["type"]
        op_cls = OperationRegistry.get(op_type)
        if not op_cls:
            raise ValueError(f"Unknown operation type: {op_type}")
        params = {k: v for k, v in op.items() if k != "type"}
        
        # 递归构建复合指令
        if op_type in ["sequence", "and", "or"] and "operations" in params:
            params["operations"] = build_operations(params["operations"])
        elif op_type == "if":
            if "then_op" in params:
                params["then_op"] = build_operations([params["then_op"]])[0]
            if "else_op" in params:
                params["else_op"] = build_operations([params["else_op"]])[0]
            if "condition_op" in params:
                params["condition_op"] = build_operations([params["condition_op"]])[0]
        elif op_type == "not" and "condition" in params:
            params["condition"] = build_operations([params["condition"]])[0]
            
        ops.append(op_cls(**params))
    return ops

@OperationRegistry.register("wait_for_new_window")
class WaitForNewWindow(Operation):
    def __init__(self, timeout=10):
        self.timeout = timeout

    def execute(self, device, context=None):
        logger.info(f"timeout={self.timeout}")
        try:
            new_handle = device.wait_for_new_window(timeout=self.timeout)
            if new_handle:
                logger.info(f"New window found and switched: {new_handle}")
                return new_handle
            else:
                logger.warning(f"No new window appeared within {self.timeout} seconds")
                return None
        except Exception as e:
            logger.error(f"Exception: {e}")
            return None

@OperationRegistry.register("wait_for_page_render")
class WaitForPageRender(Operation):
    def __init__(self, timeout=10):
        self.timeout = timeout

    def execute(self, device, context=None):
        logger.info(f"timeout={self.timeout}")
        try:
            if device.wait_for_page_load(timeout=self.timeout):
                logger.info("Page rendered successfully")
                return True
            else:
                logger.warning(f"Page did not render completely within {self.timeout} seconds")
                return False
        except Exception as e:
            logger.error(f"Exception: {e}")
            return False

@OperationRegistry.register("input_text")
class InputText(Operation):
    def __init__(self, text):
        self.text = text

    def execute(self, device, context=None):
        logger.info(f"text={self.text}")
        device.get_adb_device().shell(f"am broadcast -a ADB_INPUT_TEXT --es msg {self.text}")

# ================= 条件判断指令 =================

@OperationRegistry.register("exists")
class Exists(Operation):
    """检查元素是否存在"""
    def __init__(self, method, selector, timeout=5):
        self.method = method
        self.selector = selector
        self.timeout = timeout

    def execute(self, device, trace_id=None, context=None):
        logger.info(f"trace_id={trace_id}, method={self.method}, selector={self.selector}")
        try:
            elem = device.wait_for_element(self.method, self.selector, self.timeout, trace_id=trace_id)
            return elem is not None
        except Exception as e:
            logger.error(f"Exception: {e}")
            return False

@OperationRegistry.register("visible")
class Visible(Operation):
    """检查元素是否可见"""
    def __init__(self, method, selector, timeout=5):
        self.method = method
        self.selector = selector
        self.timeout = timeout

    def execute(self, device, trace_id=None, context=None):
        logger.info(f"trace_id={trace_id}, method={self.method}, selector={self.selector}")
        try:
            elem = device.wait_for_element(self.method, self.selector, self.timeout, trace_id=trace_id)
            return elem is not None and elem.is_displayed()
        except Exception as e:
            logger.error(f"Exception: {e}")
            return False

@OperationRegistry.register("contains_text")
class ContainsText(Operation):
    """检查元素是否包含指定文本"""
    def __init__(self, method, selector, text, timeout=5):
        self.method = method
        self.selector = selector
        self.text = text
        self.timeout = timeout

    def execute(self, device, trace_id=None, context=None):
        logger.info(f"trace_id={trace_id}, method={self.method}, selector={self.selector}, text={self.text}")
        try:
            elem = device.wait_for_element(self.method, self.selector, self.timeout, trace_id=trace_id)
            return elem is not None and self.text in elem.text
        except Exception as e:
            logger.error(f"Exception: {e}")
            return False

@OperationRegistry.register("and")
class And(Operation):
    """多个条件同时满足"""
    def __init__(self, conditions):
        self.conditions = conditions

    def execute(self, device, trace_id=None, context=None):
        logger.info(f"trace_id={trace_id}, conditions={len(self.conditions)}")
        try:
            return all(cond.execute(device, trace_id=trace_id, context=context) for cond in self.conditions)
        except Exception as e:
            logger.error(f"Exception: {e}")
            return False

@OperationRegistry.register("or")
class Or(Operation):
    """多个条件满足其一"""
    def __init__(self, conditions):
        self.conditions = conditions

    def execute(self, device, trace_id=None, context=None):
        logger.info(f"trace_id={trace_id}, conditions={len(self.conditions)}")
        try:
            return any(cond.execute(device, trace_id=trace_id, context=context) for cond in self.conditions)
        except Exception as e:
            logger.error(f"Exception: {e}")
            return False

@OperationRegistry.register("not")
class Not(Operation):
    """条件取反"""
    def __init__(self, condition):
        self.condition = condition

    def execute(self, device, trace_id=None, context=None):
        logger.info(f"trace_id={trace_id}")
        try:
            return not self.condition.execute(device, trace_id=trace_id, context=context)
        except Exception as e:
            logger.error(f"Exception: {e}")
            return False

class OperationItem:
    def __init__(self, type, **kwargs):
        self.type = type
        self.params = kwargs

    def to_dict(self):
        return {
            "type": self.type,
            **self.params
        }

    @classmethod
    def from_dict(cls, data):
        type = data.pop("type")
        return cls(type, **data)

    def build(self):
        operation_class = OperationRegistry.get(self.type)
        if not operation_class:
            raise ValueError(f"Unknown operation type: {self.type}")
        return operation_class(**self.params) 