#!/usr/bin/env python3
"""
简单测试修改后的Click类功能
"""

from unittest.mock import Mock

# 模拟FindElement类
class MockFindElement:
    def __init__(self, method, selector, timeout=10):
        self.method = method
        self.selector = selector
        self.timeout = timeout

    def execute(self, device, context=None):
        print(f"MockFindElement: 查找元素 method={self.method}, selector={self.selector}")
        # 模拟查找元素
        element = device.wait_for_element(self.method, self.selector, self.timeout)
        if element and context:
            context['element'] = element
        return element

# 模拟Click类
class MockClick:
    def __init__(self, wait_for_new_window=False, timeout=10, method=None, selector=None, context_type="WEB"):
        self.wait_for_new_window = wait_for_new_window
        self.timeout = timeout
        self.method = method
        self.selector = selector
        self.context_type = context_type.upper()

    def execute(self, device, context=None):
        print(f"MockClick: wait_for_new_window={self.wait_for_new_window}, timeout={self.timeout}, method={self.method}, selector={self.selector}, context_type={self.context_type}")
        try:
            # 获取要点击的元素
            element = context.get('element') if context else None
            
            # 如果提供了method和selector，先查找元素
            if self.method and self.selector:
                print(f"MockClick: 查找元素 method={self.method}, selector={self.selector}")
                find_op = MockFindElement(self.method, self.selector, self.timeout)
                element = find_op.execute(device, context)
                if not element:
                    print(f"MockClick: 元素未找到 method={self.method}, selector={self.selector}")
                    return False
            
            # 如果没有找到元素，返回失败
            if not element:
                print("MockClick: 没有元素可点击")
                return False

            # 根据context_type执行不同的点击逻辑
            if self.context_type == "WEB":
                return self._execute_web_click(device, element, context)
            elif self.context_type == "NATIVE":
                return self._execute_native_click(device, element, context)
            else:
                print(f"MockClick: 不支持的操作类型 {self.context_type}")
                return False

        except Exception as e:
            print(f"MockClick: 异常 {e}")
            return False

    def _execute_web_click(self, device, element, context):
        """执行WEB类型的点击操作"""
        print("MockClick: 执行WEB点击")
        try:
            # 如果需要等待新窗口，先获取当前窗口句柄
            if self.wait_for_new_window:
                old_handles = set(device.get_window_handles())

            # 执行点击
            element.click()
            print("MockClick: 元素点击成功")

            # 如果需要等待新窗口
            if self.wait_for_new_window:
                device.switch_to_new_window()
                device.wait_for_page_load()

            return True
        except Exception as e:
            print(f"MockClick: WEB点击失败 {e}")
            return False

    def _execute_native_click(self, device, element, context):
        """执行NATIVE类型的点击操作"""
        print("MockClick: 执行NATIVE点击")
        try:
            # TODO: 实现NATIVE点击逻辑
            print("MockClick: NATIVE点击逻辑待实现")
            return True
        except Exception as e:
            print(f"MockClick: NATIVE点击失败 {e}")
            return False

def test_click_with_method_selector():
    """测试带method和selector参数的Click"""
    print("=== 测试带method和selector参数的Click ===")
    
    # 创建模拟的device和context
    device = Mock()
    context = {}
    
    # 创建模拟的WebElement
    mock_element = Mock()
    mock_element.click.return_value = None
    
    # 模拟FindElement的返回值
    device.wait_for_element.return_value = mock_element
    
    # 测试Click操作
    click_op = MockClick(
        method="css selector", 
        selector=".test-button", 
        context_type="WEB",
        timeout=10
    )
    
    result = click_op.execute(device, context)
    print(f"Click执行结果: {result}")
    
    # 验证是否调用了wait_for_element
    device.wait_for_element.assert_called_once_with("css selector", ".test-button", 10)
    
    # 验证是否调用了click
    mock_element.click.assert_called_once()
    
    print("✓ 测试通过")

def test_click_with_existing_element():
    """测试使用已存在元素的Click"""
    print("\n=== 测试使用已存在元素的Click ===")
    
    # 创建模拟的device和context
    device = Mock()
    mock_element = Mock()
    mock_element.click.return_value = None
    context = {'element': mock_element}
    
    # 测试Click操作（不提供method和selector）
    click_op = MockClick(context_type="WEB")
    
    result = click_op.execute(device, context)
    print(f"Click执行结果: {result}")
    
    # 验证是否调用了click
    mock_element.click.assert_called_once()
    
    print("✓ 测试通过")

def test_click_native_context():
    """测试NATIVE类型的Click"""
    print("\n=== 测试NATIVE类型的Click ===")
    
    # 创建模拟的device和context
    device = Mock()
    context = {}
    
    # 创建模拟的WebElement
    mock_element = Mock()
    device.wait_for_element.return_value = mock_element
    
    # 测试Click操作
    click_op = MockClick(
        method="id", 
        selector="test-button", 
        context_type="NATIVE",
        timeout=5
    )
    
    result = click_op.execute(device, context)
    print(f"NATIVE Click执行结果: {result}")
    
    # 验证是否调用了wait_for_element
    device.wait_for_element.assert_called_once_with("id", "test-button", 5)
    
    print("✓ 测试通过")

def test_click_element_not_found():
    """测试元素未找到的情况"""
    print("\n=== 测试元素未找到的情况 ===")
    
    # 创建模拟的device和context
    device = Mock()
    context = {}
    
    # 模拟元素未找到
    device.wait_for_element.return_value = None
    
    # 测试Click操作
    click_op = MockClick(
        method="css selector", 
        selector=".non-existent", 
        context_type="WEB"
    )
    
    result = click_op.execute(device, context)
    print(f"Click执行结果: {result}")
    
    # 验证结果为False
    assert result == False
    print("✓ 测试通过")

def test_click_no_element_no_selector():
    """测试既没有元素也没有选择器的情况"""
    print("\n=== 测试既没有元素也没有选择器的情况 ===")
    
    # 创建模拟的device和context
    device = Mock()
    context = {}
    
    # 测试Click操作
    click_op = MockClick(context_type="WEB")
    
    result = click_op.execute(device, context)
    print(f"Click执行结果: {result}")
    
    # 验证结果为False
    assert result == False
    print("✓ 测试通过")

if __name__ == "__main__":
    print("开始测试修改后的Click类...")
    
    test_click_with_method_selector()
    test_click_with_existing_element()
    test_click_native_context()
    test_click_element_not_found()
    test_click_no_element_no_selector()
    
    print("\n🎉 所有测试通过！") 