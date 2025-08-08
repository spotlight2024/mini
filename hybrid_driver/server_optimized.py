import time
import asyncio
import json
from fastapi import FastAPI

from hybrid_driver.device_pool import DevicePool
from hybrid_driver.auto_scaler import SpotLightAutoScaler
from hybrid_driver.log_config import get_logger

# 导入路由模块
from hybrid_driver.api.routers import device, element, page, collect, mock
from hybrid_driver.native import script_executor
from hybrid_driver.operation import OperationItem, OperationSequence
from hybrid_driver.webdriver.selenium_executor import SeleniumWebExecutor

# 创建FastAPI应用
app = FastAPI(
    title="SpotLight Hybrid Driver API",
    description="混合驱动自动化测试API服务",
    version="1.0.0"
)

# 初始化全局组件
device_pool = DevicePool()
auto_scaler = SpotLightAutoScaler()
auto_scaler.start_monitoring()

logger = get_logger(__name__)

# 注册路由
app.include_router(device.router)
app.include_router(element.router)
app.include_router(page.router)
app.include_router(collect.router)
app.include_router(mock.router)

app.include_router(script_executor.commandRouter)



@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "SpotLight Hybrid Driver API",
        "version": "1.0.0",
        "docs": "/docs"
    }


def extract_restaurant_info_js(driver):
    """
    使用JavaScript注入提取当前页面的餐厅信息
    """
    js_code = """
    function extractRestaurantInfo() {
        const restaurants = [];
        const errors = [];
        
        try {
            // 等待页面加载完成
            if (document.readyState !== 'complete') {
                return {
                    success: false,
                    error: '页面未完全加载',
                    count: 0,
                    data: []
                };
            }
            
            // 查找所有餐厅项目 - 使用正确的选择器
            const shopItems = document.querySelectorAll('wx-view.shop-item.shopItem--shop-item');
            
            if (shopItems.length === 0) {
                // 尝试其他可能的选择器
                const alternativeItems = document.querySelectorAll('wx-view.shop-item');
                if (alternativeItems.length > 0) {
                    console.log('找到替代选择器的餐厅项目:', alternativeItems.length);
                    return {
                        success: false,
                        error: `找到 ${alternativeItems.length} 个替代选择器的餐厅项目，请检查选择器`,
                        count: 0,
                        data: []
                    };
                }
                return {
                    success: false,
                    error: '未找到餐厅项目',
                    count: 0,
                    data: []
                };
            }
            
            shopItems.forEach((item, index) => {
                try {
                    const restaurant = {};
                    
                                    // 查找包含餐厅信息的scroll-left元素
                const scrollLeftElem = item.querySelector('wx-view.scroll-left');
                if (!scrollLeftElem) {
                    errors.push(`餐厅${index + 1}: 未找到scroll-left元素`);
                    return;
                }
                
                // 提取餐厅名称
                const shopName = scrollLeftElem.getAttribute('data-shopname');
                if (shopName) {
                    restaurant.name = shopName;
                } else {
                    // 尝试从shop-name元素获取
                    const shopNameElem = item.querySelector('wx-view.shop-name');
                    if (shopNameElem && shopNameElem.textContent.trim()) {
                        restaurant.name = shopNameElem.textContent.trim();
                    } else {
                        errors.push(`餐厅${index + 1}: 名称缺失`);
                        return;
                    }
                }
                
                // 提取餐厅ID
                const shopId = scrollLeftElem.getAttribute('data-shopid');
                if (shopId) {
                    restaurant.shop_id = shopId;
                } else {
                    // 如果没有shop_id，使用索引作为临时ID
                    restaurant.shop_id = `temp_${index + 1}`;
                    errors.push(`餐厅${index + 1}: 使用临时ID`);
                }
                    
                    // 提取排队信息
                    const queueStatusElem = item.querySelector('wx-view.queue-status');
                    if (queueStatusElem) {
                        // 检查具体的排队状态
                        const currentStatusMsg = queueStatusElem.querySelector('wx-view.current-status-msg');
                        if (currentStatusMsg) {
                            restaurant.queue_status = currentStatusMsg.textContent.trim();
                        } else {
                            restaurant.queue_status = queueStatusElem.textContent.trim();
                        }
                        
                        // 检查等待桌数
                        const waitStatus = queueStatusElem.querySelector('wx-view.wait-status');
                        if (waitStatus) {
                            const currentStatusNum = waitStatus.querySelector('wx-view.current-status-num');
                            if (currentStatusNum) {
                                restaurant.waiting_tables = currentStatusNum.textContent.trim();
                            }
                        }
                    } else {
                        restaurant.queue_status = '状态未知';
                    }
                    
                    // 提取评分信息（如果有）
                    const starsPriceElem = item.querySelector('wx-view.stars-price');
                    if (starsPriceElem) {
                        restaurant.rating_info = starsPriceElem.textContent.trim();
                    }
                    
                    // 提取地址信息（如果有）
                    const shopAddrElem = item.querySelector('wx-view.shop-addr');
                    if (shopAddrElem) {
                        restaurant.address = shopAddrElem.textContent.trim();
                    }
                    
                    // 数据验证 - 只要有名称就添加
                    if (restaurant.name) {
                        restaurants.push(restaurant);
                    }
                    
                } catch (error) {
                    errors.push(`餐厅${index + 1}: ${error.message}`);
                }
            });
            
            return {
                success: true,
                count: restaurants.length,
                data: restaurants,
                errors: errors,
                total_found: shopItems.length
            };
            
        } catch (error) {
            return {
                success: false,
                error: error.message,
                count: 0,
                data: [],
                errors: [error.message],
                total_found: 0
            };
        }
    }
    
    return extractRestaurantInfo();
    """
    
    try:
        result = driver.execute_script(js_code)
        
        if result.get('success'):
            logger.info(f"成功提取 {result['count']} 家餐厅信息 (总共找到 {result['total_found']} 个项目)")
            if result.get('errors'):
                logger.warning(f"提取过程中的错误: {result['errors']}")
            return result['data']
        else:
            logger.error(f"提取失败: {result.get('error')}")
            return []
            
    except Exception as e:
        logger.error(f"JavaScript执行失败: {e}")
        return []


def get_current_page_restaurants(driver):
    """
    获取当前页面的餐厅信息
    """
    logger.info("开始提取餐厅信息...")

    restaurants = extract_restaurant_info_js(driver)
    
    if restaurants:
        # 打印结果
        logger.info("=== 餐厅信息提取结果 ===")
        for i, restaurant in enumerate(restaurants, 1):
            logger.info(f"{i}. {restaurant.get('name', '未知')}")
            logger.info(f"   店铺ID: {restaurant.get('shop_id', '未知')}")
            logger.info(f"   排队状态: {restaurant.get('queue_status', '未知')}")
            if 'waiting_tables' in restaurant:
                logger.info(f"   等待桌数: {restaurant['waiting_tables']}")
            if 'rating_info' in restaurant:
                logger.info(f"   评分信息: {restaurant['rating_info']}")
            if 'address' in restaurant:
                logger.info(f"   地址: {restaurant['address']}")
            logger.info("")
        
        # 保存到文件
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f'restaurants_data_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'total_count': len(restaurants),
                'data': restaurants
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"餐厅数据已保存到 {filename}")
        
    else:
        logger.warning("未提取到餐厅数据")
    
    return restaurants

async def main():
    """主函数 - 用于测试"""
    serial_id = "47.94.130.125:6521"

    # 等待连接操作完成
    from hybrid_driver.api.models import ConnectRequest
    from hybrid_driver.api.routers.device import connect

    await connect(ConnectRequest(serial_id=serial_id, user_id="10", android_process="com.tencent.mm:appbrand0"))

    # switch to current page
    device = await asyncio.get_event_loop().run_in_executor(
        None, device_pool.get, serial_id
    )
    if device is None:
        logger.error("设备未找到")
        return

    # 获取可见页面并切换
    executor: SeleniumWebExecutor = device.web_executor
    driver = executor.get_raw_remote_webdriver()
    if driver is None:
        logger.error("WebExecutor未初始化")
        return
    pages = await asyncio.get_event_loop().run_in_executor(
        None, device.web_executor.get_visible_pages
    )
    #
    logger.info(f"pages : ${pages}")



    # operations = [
    #     # 查找搜索按钮
    #     OperationItem("click", method="css selector", selector="wx-view.marketingPopup-index--button-close",
    #                   timeout=2),
    #     OperationItem("click", method="css selector", selector="wx-view.search-box.searchBox--search-box",
    #                   timeout=2),
    #
    # ]

    # sequence = OperationSequence(operations)
    # results = sequence.execute(device)

    # for i, result in enumerate(results):
    #     logger.info(f"Step {i + 1}: {'Success' if result['success'] else 'Failed'}")
    #     if not result['success']:
    #         logger.error(f"Error: {result['error']}")
    #     logger.info(f"Time: {result['elapsed']:.2f}s")

    # 添加餐厅信息提取测试
    # logger.info("开始提取餐厅信息...")
    # restaurants = await asyncio.get_event_loop().run_in_executor(
    #     None, get_current_page_restaurants, driver
    # )
    #
    # logger.info(f"餐厅信息提取完成，共获取 {len(restaurants)} 家餐厅信息")


    device.disconnect()

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
