import os
import sys
import webview
import logging
from logging.handlers import RotatingFileHandler
from backend.api_service import ApiService

# 获取日志目录
def get_log_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    log_dir = os.path.join(base_path, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return os.path.join(log_dir, 'app.log')

# 配置日志
log_file = get_log_path()
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
stream_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s',
    handlers=[file_handler, stream_handler]
)
# 屏蔽 urllib3 的 DEBUG 日志
logging.getLogger("urllib3").setLevel(logging.INFO)

logger = logging.getLogger("Main")
logger.info(f"Log file path: {log_file}")

def get_html_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'frontend', 'dist', 'index.html')
    return os.path.join(os.getcwd(), 'frontend', 'dist', 'index.html')

if __name__ == '__main__':
    api = ApiService()
    window_width = 1000
    window_height = 720
    window = webview.create_window(
        'B站直播工具',
        url=get_html_path(),
        js_api=api,
        width=window_width,
        height=window_height,
        frameless=True,
        easy_drag=False,
        hidden=True
    )
    def center_and_show_window(window):
        primary_screen = webview.screens[0]
        x = (primary_screen.width - window.width) // 2
        y = (primary_screen.height - window.height) // 2
        window.move(x, y)
        window.show()
    webview.start(center_and_show_window, window)
