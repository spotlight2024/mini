import uvicorn
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hybrid_driver.config.settings import settings

if __name__ == "__main__":
    print(f"🚀 启动 SpotLight 混合驱动服务...")
    print(f"📍 服务地址: {settings.API_HOST}:{settings.API_PORT}")
    print(f"📍 调试模式: {settings.API_RELOAD}")
    
    uvicorn.run(
        "server:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT, 
        reload=settings.API_RELOAD
    )