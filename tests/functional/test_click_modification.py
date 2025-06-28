#!/usr/bin/env python3
"""
测试修改后的Click类功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from operation import Click, FindElement
from unittest.mock import Mock, MagicMock

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
    click_op = Click(
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
    click_op = Click(context_type="WEB")
    
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
    click_op = Click(
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
    click_op = Click(
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
    click_op = Click(context_type="WEB")
    
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