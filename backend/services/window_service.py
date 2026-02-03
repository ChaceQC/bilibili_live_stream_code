import webview

class WindowService:
    def __init__(self):
        self.is_maximized = False

    def window_min(self):
        """最小化"""
        webview.windows[0].minimize()

    def window_max(self):
        """最大化/还原切换"""
        window = webview.windows[0]
        if self.is_maximized:
            window.restore()
            self.is_maximized = False
        else:
            window.maximize()
            self.is_maximized = True
        return {"code": 0, "is_maximized": self.is_maximized}

    def window_close(self, on_close_callback=None):
        """关闭程序"""
        if on_close_callback:
            on_close_callback()
        webview.windows[0].destroy()

    def get_window_position(self):
        """获取窗口当前位置"""
        window = webview.windows[0]
        return {"x": window.x, "y": window.y}

    def window_drag(self, target_x, target_y):
        """响应前端的拖拽请求，接收绝对坐标"""
        window = webview.windows[0]
        window.move(target_x, target_y)
