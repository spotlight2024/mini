import time
from abc import ABC, abstractmethod

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
    def execute(self, device, trace_id=None):
        pass

@OperationRegistry.register("find")
class FindElement(Operation):
    def __init__(self, method, selector, timeout=10):
        self.method = method
        self.selector = selector
        self.timeout = timeout

    def execute(self, device, trace_id=None):
        return device.wait_for_element(self.method, self.selector, self.timeout, trace_id=trace_id)

@OperationRegistry.register("click")
class Click(Operation):
    def __init__(self, method, selector, timeout=10):
        self.method = method
        self.selector = selector
        self.timeout = timeout

    def execute(self, device, trace_id=None):
        elem = device.wait_for_element(self.method, self.selector, self.timeout, trace_id=trace_id)
        if elem:
            elem.click()
            return True
        return False

@OperationRegistry.register("wait")
class Wait(Operation):
    def __init__(self, seconds):
        self.seconds = seconds

    def execute(self, device, trace_id=None):
        time.sleep(self.seconds)
        return True

@OperationRegistry.register("js")
class JS(Operation):
    def __init__(self, script):
        self.script = script

    def execute(self, device, trace_id=None):
        return device.driver.driver.execute_script(self.script)

@OperationRegistry.register("handle_popup")
class HandlePopup(Operation):
    def __init__(self, popup_selector, timeout=3):
        self.popup_selector = popup_selector
        self.timeout = timeout

    def execute(self, device, trace_id=None):
        try:
            popup = device.wait_for_element("css selector", self.popup_selector, self.timeout, trace_id=trace_id)
            if popup:
                popup.click()
                return True
        except Exception:
            pass
        return False

class OperationSequence:
    def __init__(self, operations):
        self.operations = operations

    def run(self, device, trace_id=None):
        results = []
        for idx, op in enumerate(self.operations):
            device.handle_common_popups(trace_id=trace_id)
            start = time.time()
            try:
                result = op.execute(device, trace_id=trace_id)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
            elapsed = time.time() - start
            results.append({
                "step": idx + 1,
                "action": op.__class__.__name__,
                "success": success,
                "result": str(result),
                "error": error,
                "elapsed": elapsed
            })
        return results

def build_operations(op_dicts):
    ops = []
    for op in op_dicts:
        op_type = op["type"]
        op_cls = OperationRegistry.get(op_type)
        if not op_cls:
            raise ValueError(f"Unknown operation type: {op_type}")
        params = {k: v for k, v in op.items() if k != "type"}
        ops.append(op_cls(**params))
    return ops 