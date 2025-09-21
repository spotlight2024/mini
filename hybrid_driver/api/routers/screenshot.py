"""
截图管理API路由 - 支持目录分类
"""
import os
import datetime
import re
from collections import defaultdict
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from hybrid_driver.log_config import get_logger

router = APIRouter(prefix="/screenshot", tags=["截图管理"])
logger = get_logger(__name__)


def get_category_from_filename(filename: str) -> str:
    """从文件名提取目录分类"""
    # 提取文件名前缀作为目录分类
    # 例如: screenshot_gongcong_xiaohao_94ecddb2db4f4e6c895ca1382d88c762.png -> gongcong_xiaohao
    # 例如: screenshot_gongcong_79a1f6e4e11844dca9a3e6804792e3ea.png -> gongcong
    
    # 移除文件扩展名
    name_without_ext = os.path.splitext(filename)[0]
    
    # 匹配截图文件名格式: screenshot_prefix_hash
    # 提取prefix部分（去掉screenshot_前缀和hash后缀）
    pattern = r'^screenshot_(.+)_[a-f0-9]{32}$'
    match = re.match(pattern, name_without_ext)
    
    if match:
        return match.group(1)  # 返回gongcong_xiaohao或gongcong
    else:
        # 如果格式不匹配，返回默认分类
        return "其他"


@router.get("/", response_class=HTMLResponse, summary="截图目录分类")
def list_screenshot_categories():
    """列出所有截图目录分类"""
    try:
        screenshot_dir = "/app/@web_screenshot"
        if not os.path.exists(screenshot_dir):
            return HTMLResponse("<h1>截图目录不存在</h1>")
        
        # 按目录分类统计文件
        categories = defaultdict(list)
        total_files = 0
        
        for filename in os.listdir(screenshot_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(screenshot_dir, filename)
                file_size = os.path.getsize(file_path)
                file_mtime = os.path.getmtime(file_path)
                category = get_category_from_filename(filename)
                
                categories[category].append({
                    'name': filename,
                    'size': file_size,
                    'mtime': file_mtime
                })
                total_files += 1
        
        # 按目录名称排序
        sorted_categories = sorted(categories.items())
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>截图目录分类</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .stats { background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .category-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .category-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; background-color: #fafafa; transition: transform 0.2s; }
        .category-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .category-title { font-size: 18px; font-weight: bold; color: #007bff; margin-bottom: 10px; }
        .category-link { display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; transition: background-color 0.2s; }
        .category-link:hover { background-color: #0056b3; }
        .file-count { color: #666; margin-bottom: 15px; }
        .back-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← 返回首页</a>
        <h1>📸 截图目录分类</h1>
        
        <div class="stats">
            <p><strong>📊 统计信息</strong></p>
            <p>总文件数: <strong>""" + str(total_files) + """</strong> 个</p>
            <p>目录分类: <strong>""" + str(len(categories)) + """</strong> 个</p>
        </div>
        
        <div class="category-grid">"""
        
        for category, files in sorted_categories:
            # 按修改时间倒序排列
            files.sort(key=lambda x: x['mtime'], reverse=True)
            latest_file = files[0] if files else None
            latest_time = datetime.datetime.fromtimestamp(latest_file['mtime']).strftime('%Y-%m-%d %H:%M:%S') if latest_file else "无"
            
            # 计算总大小
            total_size = sum(f['size'] for f in files)
            size_str = f"{total_size / 1024 / 1024:.1f} MB" if total_size > 1024 * 1024 else f"{total_size / 1024:.1f} KB"
            
            html += f"""
            <div class="category-card">
                <div class="category-title">📁 {category}</div>
                <div class="file-count">文件数: {len(files)} 个 | 总大小: {size_str}</div>
                <div style="color: #888; font-size: 14px; margin-bottom: 15px;">最新文件: {latest_time}</div>
                <a href="/screenshot/category/{category}" class="category-link">查看图片</a>
            </div>"""
        
        html += """
        </div>
    </div>
</body>
</html>"""
        
        return HTMLResponse(html)
        
    except Exception as e:
        logger.error(f"列出截图目录失败: {e}")
        return HTMLResponse(f"<h1>错误</h1><p>{str(e)}</p>")


@router.get("/category/{category}", response_class=HTMLResponse, summary="查看指定目录的截图")
def list_category_screenshots(category: str):
    """列出指定目录分类的所有截图文件"""
    try:
        screenshot_dir = "/app/@web_screenshot"
        if not os.path.exists(screenshot_dir):
            return HTMLResponse("<h1>截图目录不存在</h1>")
        
        files = []
        for filename in os.listdir(screenshot_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_category = get_category_from_filename(filename)
                if file_category == category:
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
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{category} - 截图文件</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .stats {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .preview {{ max-width: 200px; max-height: 150px; cursor: pointer; }}
        .preview:hover {{ transform: scale(1.05); transition: transform 0.2s; }}
        .file-link {{ text-decoration: none; color: #007bff; }}
        .file-link:hover {{ text-decoration: underline; }}
        .back-link {{ display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }}
        .back-link:hover {{ text-decoration: underline; }}
        .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.9); }}
        .modal-content {{ margin: auto; display: block; width: 80%; max-width: 700px; }}
        .close {{ position: absolute; top: 15px; right: 35px; color: #f1f1f1; font-size: 40px; font-weight: bold; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/screenshot/" class="back-link">← 返回目录分类</a>
        <h1>📁 {category}</h1>
        
        <div class="stats">
            <p><strong>📊 统计信息</strong></p>
            <p>文件数: <strong>{len(files)}</strong> 个</p>
        </div>
        
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
                <td><img src="/@web_screenshot/{file_info['name']}" class="preview" alt="预览" onclick="openModal('/@web_screenshot/{file_info['name']}')"></td>
            </tr>"""
        
        html += """
        </table>
    </div>
    
    <!-- 图片放大模态框 -->
    <div id="imageModal" class="modal">
        <span class="close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>
    
    <script>
        function openModal(imageSrc) {
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImage').src = imageSrc;
        }
        
        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
        }
        
        // 点击模态框外部关闭
        window.onclick = function(event) {
            var modal = document.getElementById('imageModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>"""
        
        return HTMLResponse(html)
        
    except Exception as e:
        logger.error(f"列出目录截图失败: {e}")
        return HTMLResponse(f"<h1>错误</h1><p>{str(e)}</p>")


@router.get("/all", response_class=HTMLResponse, summary="查看所有截图文件")
def list_all_screenshots():
    """列出所有截图文件（兼容原有功能）"""
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
    <title>所有截图文件</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .stats { background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .preview { max-width: 200px; max-height: 150px; cursor: pointer; }
        .preview:hover { transform: scale(1.05); transition: transform 0.2s; }
        .file-link { text-decoration: none; color: #007bff; }
        .file-link:hover { text-decoration: underline; }
        .back-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
        .category-badge { background-color: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px; margin-left: 10px; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.9); }
        .modal-content { margin: auto; display: block; width: 80%; max-width: 700px; }
        .close { position: absolute; top: 15px; right: 35px; color: #f1f1f1; font-size: 40px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/screenshot/" class="back-link">← 返回目录分类</a>
        <h1>📸 所有截图文件</h1>
        
        <div class="stats">
            <p><strong>📊 统计信息</strong></p>
            <p>总文件数: <strong>""" + str(len(files)) + """</strong> 个</p>
        </div>
        
        <table>
            <tr>
                <th>文件名</th>
                <th>分类</th>
                <th>大小</th>
                <th>修改时间</th>
                <th>预览</th>
            </tr>"""
        
        for file_info in files:
            mtime_str = datetime.datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')
            size_str = f"{file_info['size'] / 1024:.1f} KB" if file_info['size'] > 1024 else f"{file_info['size']} B"
            category = get_category_from_filename(file_info['name'])
            
            html += f"""
            <tr>
                <td><a href="/@web_screenshot/{file_info['name']}" class="file-link" target="_blank">{file_info['name']}</a></td>
                <td><span class="category-badge">{category}</span></td>
                <td>{size_str}</td>
                <td>{mtime_str}</td>
                <td><img src="/@web_screenshot/{file_info['name']}" class="preview" alt="预览" onclick="openModal('/@web_screenshot/{file_info['name']}')"></td>
            </tr>"""
        
        html += """
        </table>
    </div>
    
    <!-- 图片放大模态框 -->
    <div id="imageModal" class="modal">
        <span class="close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>
    
    <script>
        function openModal(imageSrc) {
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImage').src = imageSrc;
        }
        
        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
        }
        
        // 点击模态框外部关闭
        window.onclick = function(event) {
            var modal = document.getElementById('imageModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>"""
        
        return HTMLResponse(html)
        
    except Exception as e:
        logger.error(f"列出所有截图文件失败: {e}")
        return HTMLResponse(f"<h1>错误</h1><p>{str(e)}</p>")
