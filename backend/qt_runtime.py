"""Linux Qt 初始化，需在 pywebview 创建 QApplication 前执行。"""

import os
import sysconfig
from pathlib import Path


def _has_input_context_plugin(name, plugin_paths=None):
    # 使用 Qt 的插件搜索路径，包含 QT_PLUGIN_PATH 和 PyInstaller 打包后的目录
    # 系统 Qt 插件可能与程序自带的 Qt 不兼容，需检查能否加载
    from qtpy.QtCore import QCoreApplication, QLibraryInfo, QPluginLoader

    if plugin_paths is None:
        plugin_paths = QCoreApplication.libraryPaths()
        plugin_paths.append(QLibraryInfo.location(QLibraryInfo.PluginsPath))
    for plugin_path in dict.fromkeys(plugin_paths):
        directory = Path(plugin_path) / 'platforminputcontexts'
        for candidate in directory.glob(f'lib*{name}*platforminputcontext*.so'):
            loader = QPluginLoader(str(candidate))
            if loader.load():
                return True
    return False


def _enable_system_fcitx_plugin():
    from qtpy import QT_VERSION
    from qtpy.QtCore import QCoreApplication

    major = QT_VERSION.split('.')[0]
    candidates = [
        f'/usr/lib/qt{major}/plugins',
        f'/usr/lib64/qt{major}/plugins',
        '/usr/lib/qt/plugins',
    ]
    multiarch = sysconfig.get_config_var('MULTIARCH')
    if multiarch:
        candidates.append(f'/usr/lib/{multiarch}/qt{major}/plugins')

    for directory in candidates:
        if _has_input_context_plugin('fcitx', [directory]):
            # 将系统目录追加到末尾，优先使用程序自带的平台和渲染插件
            # Qt 会拒绝加载版本不兼容的插件
            paths = QCoreApplication.libraryPaths()
            if directory not in paths:
                QCoreApplication.setLibraryPaths([*paths, directory])
            return True
    return False


def configure_linux_qt():
    # Qt5 需要显式启用高 DPI 缩放，让 Qt 跟随桌面设置，并保留用户指定的缩放配置
    if 'QT_AUTO_SCREEN_SCALE_FACTOR' not in os.environ:
        os.environ.setdefault('QT_ENABLE_HIGHDPI_SCALING', '1')

    # PyQt5 安装包通常不包含第三方 Fcitx 插件，优先查找可加载的系统插件
    # 找不到时再尝试 Fcitx5 的 IBus 前端，保留其他输入法设置（包括显式空值）
    if os.environ.get('QT_IM_MODULE') == 'fcitx':
        if _has_input_context_plugin('fcitx') or _enable_system_fcitx_plugin():
            return
        if _has_input_context_plugin('ibus'):
            os.environ['QT_IM_MODULE'] = 'ibus'
