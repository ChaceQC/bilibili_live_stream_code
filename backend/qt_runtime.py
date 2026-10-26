"""Linux Qt setup that must run before pywebview creates QApplication."""

import os
import sysconfig
from pathlib import Path


def _has_input_context_plugin(name, plugin_paths=None):
    # Use Qt's search paths, including QT_PLUGIN_PATH and PyInstaller's relocated
    # plugin directory. A distro's Qt plugin may be incompatible with bundled Qt.
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
            # Append rather than prepend so bundled platform/rendering plugins
            # keep priority. Qt rejects plugins built for incompatible versions.
            paths = QCoreApplication.libraryPaths()
            if directory not in paths:
                QCoreApplication.setLibraryPaths([*paths, directory])
            return True
    return False


def configure_linux_qt():
    # Qt 5 high-DPI scaling is opt-in. Let Qt read the desktop's scale instead
    # of hard-coding a factor, and preserve an explicit user override.
    os.environ.setdefault('QT_ENABLE_HIGHDPI_SCALING', '1')

    # PyQt5 wheels usually omit the third-party Fcitx plugin. First look for
    # a loadable system plugin; Fcitx5's optional IBus frontend is a fallback.
    # Keep other IM selections (including an explicitly empty one) untouched.
    if os.environ.get('QT_IM_MODULE') == 'fcitx':
        if _has_input_context_plugin('fcitx') or _enable_system_fcitx_plugin():
            return
        if _has_input_context_plugin('ibus'):
            os.environ['QT_IM_MODULE'] = 'ibus'
