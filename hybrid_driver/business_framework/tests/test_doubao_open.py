"""
豆包业务测试 - 仅验证能否打开豆包页面
"""
from hybrid_driver.business_framework.business.doubao_business import DoubaoBusiness


def test_doubao_open():
    """简单测试：初始化并打开豆包首页"""
    session_id = "doubao_session_1"
    user_id = "test_user_doubao"
    doubao_business = DoubaoBusiness(session_id, user_id)

    try:
        doubao_business.initialize()
        doubao_business.initialize_pages()
        success = doubao_business.open_home_page()
        assert success, "豆包页面打开失败"
    finally:
        doubao_business.cleanup()
