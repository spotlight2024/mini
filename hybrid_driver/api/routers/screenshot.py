"""
截图管理API路由
"""
import os
import datetime
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from hybrid_driver.log_config import get_logger

router = APIRouter(prefix="/screenshot", tags=["截图管理"])
logger = get_logger(__name__)


@router.get("/", response_class=HTMLResponse, summary="截图文件列表")
def list_screenshots():
    """列出所有截图文件"""
    try:
        screenshot_dir = "/app/@web_screenshot"
        if not os.path.exists(screenshot_dir):
            return HTMLResponse("<h1>截图目录不存在</h1>")
        
        files = []
        for filename in os.listdir(screenshot_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(screenshot_dir, filename)
                file_size = os.path.getsize(file_path)
                file_mtime = os.path.getmtime(file_path)
                files.append({
                    'name': filename,
                    'size': file_size,
                    'mtime': file_mtime
                })
        
        # 按修改时间倒序排列
        files.sort(key=lambda x: x['mtime'], reverse=True)
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>截图文件列表</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .preview { max-width: 200px; max-height: 150px; }
        .file-link { text-decoration: none; color: #007bff; }
        .file-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>📸 截图文件列表</h1>
    <p>总共 <strong>""" + str(len(files)) + """</strong> 个文件</p>
    <table>
        <tr>
            <th>文件名</th>
            <th>大小</th>
            <th>修改时间</th>
            <th>预览</th>
        </tr>"""
        
        for file_info in files:
            mtime_str = datetime.datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')
            size_str = f"{file_info['size'] / 1024:.1f} KB" if file_info['size'] > 1024 else f"{file_info['size']} B"
            
            html += f"""
        <tr>
            <td><a href="/@web_screenshot/{file_info['name']}" class="file-link" target="_blank">{file_info['name']}</a></td>
            <td>{size_str}</td>
            <td>{mtime_str}</td>
            <td><img src="/@web_screenshot/{file_info['name']}" class="preview" alt="预览"></td>
        </tr>"""
        
        html += """
    </table>
</body>
</html>"""
        
        return HTMLResponse(html)
        
    except Exception as e:
        logger.error(f"列出截图文件失败: {e}")
        return HTMLResponse(f"<h1>错误</h1><p>{str(e)}</p>")
