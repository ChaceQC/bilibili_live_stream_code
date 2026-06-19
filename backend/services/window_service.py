import webview
import logging

logger = logging.getLogger("WindowService")

class WindowService:
    def __init__(self):
        # [Fix] 移除 self.window 引用，避免 pywebview 遍历 ApiService -> WindowService -> window 导致递归错误
        pass

    def _get_window(self):
        if len(webview.windows) > 0:
            return webview.windows[0]
        return None

    def window_min(self):
        window = self._get_window()
        if window:
            window.minimize()

    def window_hide(self):
        window = self._get_window()
        if window:
            window.hide()

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
