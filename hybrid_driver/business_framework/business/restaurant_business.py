"""
餐厅业务类 - 处理餐厅信息提取等业务逻辑
"""
import time
import json
import logging
from typing import List, Dict, Any, Optional
from selenium.webdriver.remote.webdriver import WebDriver

from hybrid_driver.business_framework.business.base_business import BaseBusiness
from hybrid_driver.log_config import get_logger


class RestaurantBusiness(BaseBusiness):
    """餐厅业务类 - 处理餐厅信息提取"""
    
    def __init__(self, session_id: str, user_id: str):
        # 餐厅应用配置
        site_config = {
            'site_name': 'restaurant_app',
            'home_url': '',  # 微信小程序无需URL
            'hub_url': 'http://172.16.1.129:4444/wd/hub',
            'timeout': 30,
            'implicit_wait': 10,
            'page_load_timeout': 30,
            'webdriver_mode': 'remote',
            'browser_version': '138',
            'platform_name': 'android',
            'android_package': 'com.tencent.mm',
            'android_process': 'com.tencent.mm:appbrand0'
        }
        super().__init__(site_config, session_id, user_id)
    
    def execute_business_flow(self) -> bool:
        """执行餐厅业务流程"""
        try:
            # 获取当前页面的餐厅信息
            restaurants = self.get_current_page_restaurants()
            return len(restaurants) > 0
        except Exception as e:
            self.logger.error(f"餐厅业务流程失败: {e}")
            return False
    
    def extract_restaurant_info_js(self, driver: WebDriver) -> List[Dict[str, Any]]:
        """使用JavaScript注入提取当前页面的餐厅信息"""
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

            if result.get("success"):
                self.logger.info(
                    f"成功提取 {result['count']} 家餐厅信息 (总共找到 {result['total_found']} 个项目)"
                )
                if result.get("errors"):
                    self.logger.warning(f"提取过程中的错误: {result['errors']}")
                return result["data"]
            else:
                self.logger.error(f"提取失败: {result.get('error')}")
                return []

        except Exception as e:
            self.logger.error(f"JavaScript执行失败: {e}")
            return []

    def get_current_page_restaurants(self) -> List[Dict[str, Any]]:
        """获取当前页面的餐厅信息"""
        self.logger.info("开始提取餐厅信息...")
        
        driver = self.get_driver()
        if not driver:
            self.logger.error("WebDriver未初始化")
            return []

        restaurants = self.extract_restaurant_info_js(driver)

        if restaurants:
            # 打印结果
            self.logger.info("=== 餐厅信息提取结果 ===")
            for i, restaurant in enumerate(restaurants, 1):
                self.logger.info(f"{i}. {restaurant.get('name', '未知')}")
                self.logger.info(f"   店铺ID: {restaurant.get('shop_id', '未知')}")
                self.logger.info(f"   排队状态: {restaurant.get('queue_status', '未知')}")
                if "waiting_tables" in restaurant:
                    self.logger.info(f"   等待桌数: {restaurant['waiting_tables']}")
                if "rating_info" in restaurant:
                    self.logger.info(f"   评分信息: {restaurant['rating_info']}")
                if "address" in restaurant:
                    self.logger.info(f"   地址: {restaurant['address']}")
                self.logger.info("")

            # 保存到文件
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"restaurants_data_{timestamp}.json"

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "timestamp": timestamp,
                        "total_count": len(restaurants),
                        "data": restaurants,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            self.logger.info(f"餐厅数据已保存到 {filename}")

        else:
            self.logger.warning("未提取到餐厅数据")

        return restaurants
