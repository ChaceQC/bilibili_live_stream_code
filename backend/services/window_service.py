import sys
import webview
import logging

logger = logging.getLogger("WindowService")

class WindowService:
    def __init__(self):
        self._hwnd = None  # 由 main.py 在窗口创建后注入（仅 Windows）

    def set_hwnd(self, hwnd):
        """由 main.py 注入主窗口 HWND"""
        self._hwnd = hwnd

    def _get_window(self):
        if len(webview.windows) > 0:
            return webview.windows[0]
        return None

    def window_min(self):
        window = self._get_window()
        if window:
            window.minimize()

    def window_max(self):
        window = self._get_window()
        if window:
            # pywebview 没有直接的 is_maximized 属性，这里简单切换
            # 实际逻辑可能需要前端配合记录状态，或者 toggle_fullscreen
            # 这里暂时只做 toggle
            window.toggle_fullscreen()
            return {"is_maximized": True} # 简化返回
        return {"is_maximized": False}

    def window_close(self, save_callback=None):
        if save_callback:
            save_callback()
        window = self._get_window()
        if window:
            window.destroy()
        return True

    def get_window_position(self):
        window = self._get_window()
        if window:
            return {"x": window.x, "y": window.y}
        return {"x": 0, "y": 0}

    def window_drag(self, target_x, target_y):
        window = self._get_window()
        if window:
            window.move(target_x, target_y)

    def send_to_frontend(self, function_name, data):
        """发送数据到前端"""
        window = self._get_window()
        if window:
            # 使用 evaluate_js 调用前端挂载在 window 上的函数
            # 注意数据需要序列化
            import json
            json_data = json.dumps(data)
            # 这里的引号处理要小心
            js_code = f"if(window.{function_name}) window.{function_name}({json_data})"
            try:
                window.evaluate_js(js_code)
            except Exception:
                # 忽略窗口关闭期间无法执行 JS 的错误 (如 ObjectDisposedException)
                pass

    # --- 透明度 & 置顶（仅 Windows，通过 WinAPI 实现）---

    def _get_hwnd(self):
        """获取主窗口 HWND。优先使用 main.py 注入值，否则枚举当前进程的顶级可见窗口。"""
        if self._hwnd:
            return self._hwnd

        import ctypes
        import os
        from ctypes import wintypes

        current_pid = os.getpid()
        found = []

        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32 = ctypes.windll.user32

        def enum_cb(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == current_pid:
                found.append(hwnd)
            return True

        user32.EnumWindows(EnumWindowsProc(enum_cb), 0)

        if found:
            # 取第一个可见顶级窗口
            hwnd = found[0]
            logger.info(f"_get_hwnd: found via EnumWindows hwnd={hwnd:#x}")
            self._hwnd = hwnd
            return hwnd

        logger.warning("_get_hwnd: no HWND found")
        return None

    def set_window_opacity(self, opacity_percent):
        """设置窗口整体不透明度，opacity_percent: 0~100"""
        if sys.platform != 'win32':
            return {"code": -1, "msg": "仅支持 Windows"}

        import ctypes
        hwnd = self._get_hwnd()
        if not hwnd:
            return {"code": -1, "msg": "HWND 未找到，请重启应用"}

        GWL_EXSTYLE   = -20
        WS_EX_LAYERED = 0x00080000
        LWA_ALPHA     = 0x00000002

        # 限制最低 20，避免窗口完全消失
        alpha = max(51, min(255, int(opacity_percent * 255 / 100)))

        user32 = ctypes.windll.user32
        # 用 PtrW 版本，64 位安全
        user32.GetWindowLongPtrW.restype = ctypes.c_longlong
        user32.SetWindowLongPtrW.restype = ctypes.c_longlong
        ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)

        user32.SetLayeredWindowAttributes.restype = ctypes.c_bool
        result = user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)
        logger.info(f"set_window_opacity: {opacity_percent}%  alpha={alpha}  ok={result}")
        if not result:
            err = ctypes.GetLastError()
            return {"code": -1, "msg": f"SetLayeredWindowAttributes 失败，LastError={err}"}
        return {"code": 0}

    def set_window_topmost(self, on_top):
        """设置窗口是否置顶"""
        if sys.platform != 'win32':
            return {"code": -1, "msg": "仅支持 Windows"}

        import ctypes
        hwnd = self._get_hwnd()
        if not hwnd:
            return {"code": -1, "msg": "HWND 未找到，请重启应用"}

        # 必须用 c_void_p 包装，否则 64 位下 -1/-2 会被截断为无效地址
        HWND_TOPMOST   = ctypes.c_void_p(-1)
        HWND_NOTOPMOST = ctypes.c_void_p(-2)
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001

        insert_after = HWND_TOPMOST if on_top else HWND_NOTOPMOST
        ctypes.windll.user32.SetWindowPos(hwnd, insert_after, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        logger.info(f"set_window_topmost: on_top={on_top}")
        return {"code": 0}
