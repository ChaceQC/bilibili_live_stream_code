import os
import sys

# [修复] 根据平台设置不同的环境变量
if sys.platform == 'linux':
    # Linux: 强制使用 x11 后端 (XWayland)
    # 1. GDK_BACKEND=x11: 修复 Wayland 下 GTK 托盘初始化崩溃 "Can't create GtkStyleContext without display"
    # 2. QT_QPA_PLATFORM=xcb: 强制 Qt 使用 X11 后端，确保窗口拖动 (window.move) 和位置控制在 Wayland 下正常工作
    os.environ["GDK_BACKEND"] = "x11"
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    # [Fix] 强制使用 Fusion 风格，防止 Qt 尝试加载 GTK 主题 (QGtkStyle) 导致崩溃
    os.environ["QT_STYLE_OVERRIDE"] = "Fusion"
    # [Fix] 禁用平台主题插件 (如 qt5ct, gtk2)，防止它们加载 GTK
    if "QT_QPA_PLATFORMTHEME" in os.environ:
        del os.environ["QT_QPA_PLATFORMTHEME"]
elif sys.platform == 'darwin':
    # macOS: 使用原生 cocoa 后端
    os.environ["QT_QPA_PLATFORM"] = "cocoa"
    # 禁用 GTK 后端
    if "QT_QPA_PLATFORMTHEME" in os.environ:
        del os.environ["QT_QPA_PLATFORMTHEME"]

import webview
import logging
from logging.handlers import RotatingFileHandler
from backend.api_service import ApiService

def get_log_xdg_base_path():
    """
    获取 XDG 标准的 log base path
    """
    # 获取 XDG 标准的 DATA_HOME
    data_home = os.environ.get('XDG_DATA_HOME')

    if not data_home or data_home == '':
        # 默认回退
        data_home = os.path.expanduser('~/.local/share')

    base_path = os.path.join(data_home, "BiliLiveTool")
    return base_path

# 获取日志目录
def get_log_path():
    if sys.platform.startswith('linux'):
        base_path = get_log_xdg_base_path()
    elif getattr(sys, 'frozen', False):
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

# 启用高 DPI 感知，确保在高分辨率显示器上的正确缩放
def _enable_windows_dpi_awareness():
    import ctypes
    # 先尝试 PMv2
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass

    # Fallback: Per-monitor aware
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    # Fallback: System DPI aware
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

def _get_primary_monitor_scale_win():
    import ctypes
    from ctypes import wintypes

    try:
        shcore = ctypes.windll.shcore
        user32 = ctypes.windll.user32

        hwnd = user32.GetDesktopWindow()
        hmon = user32.MonitorFromWindow(hwnd, 1)

        MDT_EFFECTIVE_DPI = 0
        dpi_x = wintypes.UINT()
        dpi_y = wintypes.UINT()
        shcore.GetDpiForMonitor(hmon, MDT_EFFECTIVE_DPI, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
        return dpi_x.value / 96.0
    except Exception:
        return 1.0

if __name__ == '__main__':
    api = ApiService()
    window_width = 1000
    window_height = 720
    scale = 1.0
    if sys.platform == 'win32':
        _enable_windows_dpi_awareness()
        scale = _get_primary_monitor_scale_win()
    window = webview.create_window(
        'B站直播工具',
        url=get_html_path(),
        js_api=api,
        width=window_width,
        height=window_height,
        frameless=True,
        easy_drag=False, # 仅通过 pywebview-drag-region CSS 类标记拖拽区域
        # hidden=True
    )
    def center_and_show_window(window):
        primary_screen = webview.screens[0]
        if sys.platform == 'win32':
            screen_w = int(primary_screen.width / scale)
            screen_h = int(primary_screen.height / scale)
        else:
            screen_w = primary_screen.width
            screen_h = primary_screen.height

        x = (screen_w - window_width) // 2
        y = (screen_h - window_height) // 2
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
                    # style &= ~0x00040000
                    # 但我们现在需要使窗口可以 resize
                    style |= 0x00040000  # WS_THICKFRAME
                    
                    # 2. 添加 WS_MINIMIZEBOX (0x00020000) 以支持任务栏点击最小化
                    style |= 0x00020000 
                    
                    user32.SetWindowLongW(hwnd, -16, style)
                    
                    # 刷新窗口状态
                    # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
                    user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0004 | 0x0020)

                    # 注入 HWND 到 window_service，供透明度/置顶 API 使用
                    api.window_service.set_hwnd(hwnd)
            except Exception as e:
                logger.error(f"Failed to set window style: {e}")

        window.show()

        # [Fix] Linux (Qt backend): 防止隐藏最后一个窗口时 Qt 自动退出
        if sys.platform != 'win32':
            try:
                from qtpy.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    app.setQuitOnLastWindowClosed(False)
            except Exception as e:
                print(f"Failed to set quitOnLastWindowClosed: {e}")

    # --- 全局清理逻辑 ---
    def cleanup_services(api_service):
        """执行清理工作：停止直播、停止弹幕、保存配置"""
        try:
            # 1. 停止直播
            if api_service.session_state.is_live:
                api_service.live_service.stop_live()
            
            # 2. 停止弹幕
            import asyncio
            if api_service.loop:
                 asyncio.run_coroutine_threadsafe(api_service.danmu_service.stop(), api_service.loop)

            # 3. 保存配置
            api_service.config_manager.save()
            print("Services cleaned up.")
        except Exception as e:
            print(f"Cleanup failed: {e}")

    # --- 全局标志 ---
    import threading
    tray_state = {'is_exiting': False, 'tray_active': False}
    tray_icon = None  # Windows pystray icon 引用

    # --- 通用托盘回调（跨平台共享） ---
    def tray_show_window():
        import time
        window.show()
        time.sleep(0.1)
        window.restore()
        # 通知前端恢复轮询等操作
        try:
            api.window_service.send_to_frontend("onAppShown", None)
        except Exception:
            pass

    def tray_start_live():
        user_config = api.user_service.load_saved_config()
        if user_config and 'last_area_name' in user_config:
            area = user_config['last_area_name']
            if isinstance(area, list) and len(area) >= 2:
                res = api.start_live(area[0], area[1])
            else:
                res = api.start_live()
        else:
            res = api.start_live()

        # 恢复并显示窗口
        window.restore()
        window.show()

        # 根据返回结果推送事件到前端
        if res and res.get('code') == 0:
            api.window_service.send_to_frontend("onTrayLiveStarted", res.get('data'))
        elif res and res.get('code') == 60024:
            api.window_service.send_to_frontend("onTrayNeedFaceVerify", res.get('qr', ''))
        else:
            msg = res.get('msg', '开播失败') if res else '开播失败'
            api.window_service.send_to_frontend("onTrayLiveError", msg)

    def tray_stop_live():
        res = api.stop_live()
        if res and res.get('code') == 0:
            api.window_service.send_to_frontend("onTrayLiveStopped", None)

    def tray_exit():
        global tray_icon
        tray_state['is_exiting'] = True

        # 停止托盘图标
        if sys.platform == 'win32':
            if tray_icon:
                tray_icon.stop()
        else:
            # Linux Qt cleanup
            if tray_icon:
                try:
                    tray_icon.hide()
                except Exception:
                    pass

        print("Tray exit clicked. Cleaning up...")
        cleanup_services(api)

        print("Exiting application via Tray...")
        os._exit(0)

    # --- 通用 on_closing（跨平台共享） ---
    def on_closing():
        try:
            if tray_state['is_exiting']:
                return True  # 正在退出，允许关闭

            # 检查配置
            min_to_tray = True
            try:
                min_to_tray = api.config_manager.data.get("min_to_tray", True)
            except Exception as e:
                print(f"Error reading config: {e}")

            if min_to_tray and tray_state.get('tray_active', False):
                # 最小化到托盘
                if sys.platform == 'win32':
                    window.hide()
                else:
                    # [Fix] Linux Qt backend: hide() 可能导致窗口无法恢复，用 minimize 代替
                    window.minimize()
                # [Fix] 异步通知前端暂停轮询，不能同步调用 evaluate_js，否则在 UI 线程死锁
                threading.Thread(
                    target=lambda: api.window_service.send_to_frontend("onAppHidden", None),
                    daemon=True
                ).start()
                return False  # 阻止窗口关闭
            else:
                # 直接退出模式
                tray_state['is_exiting'] = True
                if sys.platform == 'win32' and tray_icon:
                    tray_icon.stop()

                cleanup_services(api)

                # [Fix] Linux 下必须强制退出，否则后台线程（asyncio loop 等）导致 SIGABRT
                if sys.platform != 'win32':
                    print("Exiting application...")
                    os._exit(0)

                return True  # 允许窗口关闭 (pywebview 会退出)
        except Exception as e:
            print(f"Error in on_closing: {e}")
            return True

    window.events.closing += on_closing

    # --- 托盘图标逻辑 (平台分支) ---
    if sys.platform == 'win32':
        def create_tray_icon_win(window_obj):
            try:
                from PIL import Image
                import pystray
                from pystray import MenuItem as item
            except ImportError as e:
                print(f"Failed to import tray dependencies: {e}")
                return None

            def on_show(icon, item): tray_show_window()
            def on_start(icon, item): tray_start_live()
            def on_stop(icon, item): tray_stop_live()
            def on_quit(icon, item): tray_exit()

            # 加载图标
            icon_image = None
            try:
                if getattr(sys, 'frozen', False):
                    icon_path = os.path.join(sys._MEIPASS, 'bilibili.ico')
                else:
                    icon_path = os.path.join(os.getcwd(), 'bilibili.ico')
                icon_image = Image.open(icon_path)
            except Exception as e:
                logger.error(f"Failed to load tray icon: {e}")
                icon_image = Image.new('RGB', (64, 64), color='red')

            menu = pystray.Menu(
                item('显示主界面', on_show, default=True),
                item('开始直播', on_start),
                item('停止直播', on_stop),
                item('退出程序', on_quit)
            )

            icon = pystray.Icon("BiliLiveTool", icon_image, "B站直播工具", menu)
            return icon

        def run_tray_win():
            global tray_icon
            icon = create_tray_icon_win(window)
            if icon:
                tray_icon = icon
                tray_state['tray_active'] = True
                api.tray_active = True  # 同步到 api_service
                tray_icon.run()

    # Windows 托盘在独立线程启动
    if sys.platform == 'win32':
        threading.Thread(target=run_tray_win, daemon=True).start()
    
    # --- Linux 托盘 (Qt Native) ---
    def create_tray_icon_linux():
        try:
            from qtpy.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
            from qtpy.QtGui import QIcon
            from qtpy.QtCore import QObject, Slot, Qt, QMetaObject
        except ImportError:
            print("Qt dependencies not found. Tray disabled.")
            return

        global tray_icon
        
        # 此时 webview 已经启动，QApplication 必然存在
        app = QApplication.instance()
        
        if not app:
            # 尝试多等一下?
            import time
            for _ in range(5):
                app = QApplication.instance()
                if app: break
                time.sleep(0.1)
        
        if not app:
            print("QApplication not running. Tray disabled.")
            return

        # 定义在主线程运行的 Setup 逻辑
        class TraySetup(QObject):
            @Slot()
            def run(self):
                # 图标路径
                if getattr(sys, 'frozen', False):
                    base_path = sys._MEIPASS
                else:
                    base_path = os.getcwd()
                
                icon_path = os.path.join(base_path, 'bilibili.ico')
                # Qt 在 Linux 上通常支持 png，ico 取决于插件。提供 png fallback
                if not os.path.exists(icon_path):
                        icon_path = os.path.join(base_path, 'bilibili.png')
                
                icon = QSystemTrayIcon(app)
                if os.path.exists(icon_path):
                    icon.setIcon(QIcon(icon_path))
                else:
                    print(f"Tray icon not found at {icon_path}")
                    
                icon.setToolTip("B站直播工具")
                
                menu = QMenu()
                
                a_show = QAction("显示主界面", menu)
                a_show.triggered.connect(lambda: threading.Thread(target=tray_show_window, daemon=True).start())
                menu.addAction(a_show)
                
                menu.addSeparator()
                
                a_start = QAction("开始直播", menu)
                a_start.triggered.connect(lambda: threading.Thread(target=tray_start_live, daemon=True).start())
                menu.addAction(a_start)
                
                a_stop = QAction("停止直播", menu)
                a_stop.triggered.connect(lambda: threading.Thread(target=tray_stop_live, daemon=True).start())
                menu.addAction(a_stop)
                
                menu.addSeparator()
                
                a_exit = QAction("退出程序", menu)
                a_exit.triggered.connect(lambda: tray_exit()) 
                menu.addAction(a_exit)
                
                icon.setContextMenu(menu)
                
                def on_activated(reason):
                    if reason == QSystemTrayIcon.Trigger:
                        threading.Thread(target=tray_show_window, daemon=True).start()
                icon.activated.connect(on_activated)
                
                icon.show()
                
                global tray_icon
                tray_icon = icon
                
                tray_state['tray_active'] = True
                api.tray_active = True
                print("Linux Qt Tray started.")

        # 3. 将 Setup 移动到主线程执行
        setup_obj = TraySetup()
        setup_obj.moveToThread(app.thread())
        app._tray_setup = setup_obj # 防止 GC
        
        QMetaObject.invokeMethod(setup_obj, "run", Qt.QueuedConnection)

    # 定义启动回调：先显示窗口，再初始化 Linux 托盘
    def on_app_start(window_obj=None):
        if window_obj:
            center_and_show_window(window_obj)
        else:
            center_and_show_window(window) # Fallback to global if None passed
            
        if sys.platform != 'win32':
             # 允许通过环境变量禁用托盘，方便排查崩溃问题
            if os.environ.get("DISABLE_TRAY", "0") == "1":
                print("Linux tray disabled by environment variable.")
                return

            try:
                # 检查托盘是否可用 (虽然这不一定能防住崩溃)
                from qtpy.QtWidgets import QSystemTrayIcon
                if not QSystemTrayIcon.isSystemTrayAvailable():
                     print("System tray report unavailable. Skipping tray creation.")
                     return
                
                # 在 webview 启动后创建托盘
                create_tray_icon_linux()
            except Exception as e:
                print(f"Failed to create Linux tray: {e}")

    # [Fix] 强制 Linux 使用 Qt 后端，确保与 QSystemTrayIcon 兼容
    # Windows 保持默认 (Edge/CEF)
    gui_backend = 'qt' if sys.platform != 'win32' else None
    webview.start(on_app_start, window, gui=gui_backend)

