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
        
        # [修复] Windows 下无边框窗口无法通过任务栏图标最小化的问题
        if sys.platform == 'win32':
            try:
                import ctypes
                hwnd = None
                
                # 辅助函数：尝试将 Handle 转换为 int
                def get_hwnd(handle):
                    # 如果是 C# IntPtr 对象 (pythonnet)，通常有 ToInt64 方法
                    if hasattr(handle, 'ToInt64'):
                        return handle.ToInt64()
                    # 或者是 ToInt32
                    elif hasattr(handle, 'ToInt32'):
                        return handle.ToInt32()
                    else:
                        return int(handle)

                # 尝试获取窗口句柄 (兼容不同 pywebview 版本)
                if hasattr(window, 'gui') and hasattr(window.gui, 'Handle'):
                    hwnd = get_hwnd(window.gui.Handle)
                elif hasattr(window, 'native') and hasattr(window.native, 'Handle'):
                    hwnd = get_hwnd(window.native.Handle)
                
                if hwnd:
                    # GWL_STYLE = -16
                    user32 = ctypes.windll.user32
                    style = user32.GetWindowLongW(hwnd, -16)
                    
                    # 1. 去除 WS_THICKFRAME (0x00040000) 以消除顶部白条
                    #    之前的尝试中添加了这个样式导致了白条
                    style &= ~0x00040000
                    
                    # 2. 添加 WS_MINIMIZEBOX (0x00020000) 以支持任务栏点击最小化
                    style |= 0x00020000 
                    
                    user32.SetWindowLongW(hwnd, -16, style)
                    
                    # 刷新窗口状态
                    # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
                    user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0004 | 0x0020)
            except Exception as e:
                logger.error(f"Failed to set window style: {e}")

        window.show()
    webview.start(center_and_show_window, window)
