import os
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.qt_runtime import configure_linux_qt, _has_input_context_plugin


class LinuxQtTests(unittest.TestCase):
    def test_real_qt_screen_scaling(self):
        # Qt 在创建应用时读取 DPI 设置，同一进程中不能安全地重复创建
        # 每组设置使用独立进程验证
        script = '''
import json
from backend.qt_runtime import configure_linux_qt
configure_linux_qt()
from qtpy.QtWidgets import QApplication, QWidget
app = QApplication([])
window = QWidget()
window.resize(400, 300)
print(json.dumps([app.primaryScreen().devicePixelRatio(), window.width(), window.height()]))
'''
        for dpi, overrides, expected in [
            ('96', {}, 1.0),
            ('192', {}, 2.0),
            ('192', {'QT_ENABLE_HIGHDPI_SCALING': '0'}, 1.0),
            ('192', {'QT_AUTO_SCREEN_SCALE_FACTOR': '0'}, 1.0),
            ('192', {'QT_AUTO_SCREEN_SCALE_FACTOR': '1'}, 2.0),
            ('96', {'QT_SCALE_FACTOR': '1.5'}, 1.5),
        ]:
            with self.subTest(dpi=dpi, overrides=overrides):
                env = {key: value for key, value in os.environ.items() if not key.startswith('QT_')}
                env.update(QT_QPA_PLATFORM='offscreen', QT_FONT_DPI=dpi)
                env.update(overrides)
                result = subprocess.run(
                    [sys.executable, '-c', script], env=env, check=True,
                    capture_output=True, text=True, timeout=15,
                    cwd=Path(__file__).resolve().parents[1],
                )
                self.assertEqual(json.loads(result.stdout), [expected, 400, 300])

    def test_scaling_defaults_to_enabled(self):
        with patch.dict(os.environ, {}, clear=True):
            configure_linux_qt()
            self.assertEqual(os.environ['QT_ENABLE_HIGHDPI_SCALING'], '1')
            self.assertNotIn('QT_SCALE_FACTOR', os.environ)
            self.assertNotIn('QT_IM_MODULE', os.environ)

    def test_explicit_scaling_overrides_are_preserved(self):
        values = {'QT_ENABLE_HIGHDPI_SCALING': '0', 'QT_SCALE_FACTOR': '1.5'}
        with patch.dict(os.environ, values, clear=True):
            configure_linux_qt()
            self.assertEqual(dict(os.environ), values)

    def test_fcitx_falls_back_only_when_ibus_is_available(self):
        for available, expected in [({'ibus'}, 'ibus'), ({'fcitx', 'ibus'}, 'fcitx'), (set(), 'fcitx')]:
            with self.subTest(available=available), patch.dict(os.environ, {'QT_IM_MODULE': 'fcitx'}, clear=True):
                with patch('backend.qt_runtime._has_input_context_plugin', side_effect=lambda name: name in available):
                    with patch('backend.qt_runtime._enable_system_fcitx_plugin', return_value=False):
                        configure_linux_qt()
                self.assertEqual(os.environ['QT_IM_MODULE'], expected)

    def test_system_fcitx_is_preferred_over_ibus(self):
        with patch.dict(os.environ, {'QT_IM_MODULE': 'fcitx'}, clear=True):
            with patch('backend.qt_runtime._has_input_context_plugin', return_value=False):
                with patch('backend.qt_runtime._enable_system_fcitx_plugin', return_value=True):
                    configure_linux_qt()
            self.assertEqual(os.environ['QT_IM_MODULE'], 'fcitx')

    def test_system_plugin_path_preserves_bundled_plugin_priority(self):
        from backend.qt_runtime import _enable_system_fcitx_plugin

        with patch('backend.qt_runtime._has_input_context_plugin', return_value=True):
            with patch('qtpy.QtCore.QCoreApplication.libraryPaths', return_value=['/bundled/plugins']):
                with patch('qtpy.QtCore.QCoreApplication.setLibraryPaths') as set_paths:
                    self.assertTrue(_enable_system_fcitx_plugin())
                    self.assertEqual(set_paths.call_args.args[0][0], '/bundled/plugins')

    def test_other_input_method_selections_are_preserved(self):
        for selection in ['', 'ibus', 'xim', 'wayland']:
            with self.subTest(selection=selection), patch.dict(os.environ, {'QT_IM_MODULE': selection}, clear=True):
                with patch('backend.qt_runtime._has_input_context_plugin') as probe:
                    configure_linux_qt()
                    probe.assert_not_called()
                self.assertEqual(os.environ['QT_IM_MODULE'], selection)

    def test_plugin_probe_uses_qt_paths_and_rejects_unloadable_plugins(self):
        from qtpy.QtCore import QLibraryInfo

        with tempfile.TemporaryDirectory() as directory:
            plugins = Path(directory) / 'platforminputcontexts'
            plugins.mkdir()
            (plugins / 'libfcitx5platforminputcontextplugin.so').write_text('not a Qt plugin')
            with patch('qtpy.QtCore.QCoreApplication.libraryPaths', return_value=[directory]):
                with patch.object(QLibraryInfo, 'location', return_value=directory):
                    self.assertFalse(_has_input_context_plugin('fcitx'))


if __name__ == '__main__':
    unittest.main()
