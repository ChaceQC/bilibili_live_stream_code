import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from backend.services.window_service import WindowService


class WindowDragTests(unittest.TestCase):
    def test_non_linux_uses_coordinate_fallback(self):
        with patch('backend.services.window_service.sys.platform', 'win32'):
            self.assertFalse(WindowService().window_set_drag_region(32, 138))

    def test_missing_window_uses_coordinate_fallback(self):
        service = WindowService()
        with patch.object(service, '_get_window', return_value=None):
            self.assertFalse(service.window_set_drag_region(32, 138))

    def test_native_titlebar_events_and_gui_thread_installation(self):
        script = """
import threading
from types import SimpleNamespace
from qtpy.QtCore import QThread, QTimer, QPoint, Qt
from qtpy.QtWidgets import QApplication, QWidget
from qtpy.QtTest import QTest
from backend.qt_window import set_drag_region
app = QApplication([])
window = QWidget()
window.resize(1000, 720)
child = QWidget(window)
child.resize(1000, 720)
calls = []
def move():
    assert QThread.currentThread() == app.thread()
    calls.append(True)
    return True
window.windowHandle = lambda: SimpleNamespace(startSystemMove=move)
result = []
def worker():
    result.append(set_drag_region(window, 32, 138))
    app.quit()
thread = threading.Thread(target=worker, daemon=True)
thread.start()
QTimer.singleShot(5000, app.quit)
app.exec_()
thread.join(1)
assert result == [True], result
QTest.mouseClick(child, Qt.LeftButton, pos=QPoint(100, 15))
assert len(calls) == 1, calls
# 窗口控制按钮、正文、其他鼠标按键及其他窗口的输入不应被拦截
QTest.mouseClick(child, Qt.LeftButton, pos=QPoint(950, 15))
QTest.mouseClick(child, Qt.LeftButton, pos=QPoint(100, 100))
QTest.mouseClick(child, Qt.RightButton, pos=QPoint(100, 15))
other = QWidget()
QTest.mouseClick(other, Qt.LeftButton, pos=QPoint(10, 10))
assert len(calls) == 1, calls
# 重复注册只更新区域，不重复安装事件过滤器
handler = window._bili_move_filter
assert set_drag_region(window, 40, 200)
assert window._bili_move_filter is handler
QTest.mouseClick(child, Qt.LeftButton, pos=QPoint(850, 15))
assert len(calls) == 1, calls
"""
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
        subprocess.run(
            [sys.executable, '-c', script], check=True, env=env,
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, timeout=10,
        )
