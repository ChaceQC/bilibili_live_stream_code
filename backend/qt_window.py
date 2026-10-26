"""Qt window gestures must start during native mouse event dispatch."""

import logging
from qtpy.QtCore import QObject, QEvent, Qt, QThread, QMetaObject, Q_RETURN_ARG, Slot
from qtpy.QtWidgets import QApplication, QWidget

logger = logging.getLogger('QtWindow')


class _MoveFilter(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.height = 0
        self.right_inset = 0

    def eventFilter(self, watched, event):
        if (event.type() == QEvent.MouseButtonPress
                and event.button() == Qt.LeftButton
                and isinstance(watched, QWidget)
                and watched.window() == self.window):
            point = watched.mapTo(self.window, event.pos())
            if (0 <= point.y() < self.height
                    and 0 <= point.x() < self.window.width() - self.right_inset):
                handle = self.window.windowHandle()
                started = bool(handle and handle.startSystemMove())
                logger.debug('Native mouse system move accepted: %s', started)
                # Consume the press only after the compositor accepts the move.
                # Otherwise the frontend can use its coordinate-based fallback.
                return started
        return False


def set_drag_region(window, height, right_inset):
    """Install/update the titlebar hit area on Qt's GUI thread."""
    app = QApplication.instance()
    if app is None:
        return False

    def install():
        handler = getattr(window, '_bili_move_filter', None)
        if handler is None:
            handler = _MoveFilter(window)
            window._bili_move_filter = handler
            app.installEventFilter(handler)
        handler.height = max(0, float(height))
        handler.right_inset = max(0, float(right_inset))
        return True

    if QThread.currentThread() == app.thread():
        return install()

    class Setup(QObject):
        @Slot(result=bool)
        def run(self):
            try:
                return install()
            except Exception:
                logger.exception('Could not install native titlebar move handler')
                return False

    task = Setup()
    task.moveToThread(app.thread())
    try:
        return QMetaObject.invokeMethod(
            task, 'run', Qt.BlockingQueuedConnection, Q_RETURN_ARG(bool),
        )
    finally:
        task.deleteLater()
