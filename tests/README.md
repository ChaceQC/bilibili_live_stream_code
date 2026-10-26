# Linux Qt 验证（issue #56）

安装后端依赖后，从仓库根目录运行：

```bash
python -m unittest discover -s tests -v
```

测试覆盖输入法插件回退、保留用户配置，以及独立 Qt 进程在 96/192 DPI 和显式缩放设置下的实际设备像素比。窗口始终使用逻辑尺寸，避免重复放大。

输入法规则优先使用 Qt 自身的插件路径（含 `QT_PLUGIN_PATH` 和打包后的路径），再检查常见系统目录中的 Fcitx 插件，并验证动态库能否加载。系统路径追加在自带插件路径之后，保持原平台插件的优先级。存在但无法加载的 Fcitx 插件不会阻止回退；没有可用的 IBus 插件时保留原设置。

仍需在桌面环境中进行以下人工验证，源码运行和 Linux 发布包均需检查：

1. Fedora GNOME Wayland + Fcitx5，桌面缩放分别设为 100% 和 200%，确认窗口及网页内容同步缩放。
2. 使用 `QT_IM_MODULE=fcitx` 启动，在直播标题、弹幕等输入框切换中英文，检查候选框、选词提交、退格和再次切换。应优先使用兼容的系统 Fcitx Qt 插件。没有 Fcitx 插件时，另行确认 IBus 回退是否能连接 Fcitx5 服务，不能仅凭动态库可加载判定输入正常。
3. 在装有兼容 Fcitx Qt 插件的环境中重复输入测试，确认继续使用 Fcitx。
4. 在 X11/XWayland 和 KDE Wayland 下确认启动及输入正常；KDE 未设置 `QT_IM_MODULE` 时应保留桌面默认行为。

原生拖动过滤器只在 Qt 的 `wayland` 平台启用。Windows、macOS 和 X11/XWayland 保留原有前端指针捕获代码、拖动区域类名及样式。

可使用 `QT_DEBUG_PLUGINS=1` 查看加载的 `platforminputcontexts` 插件。自动化测试不覆盖真实输入法服务的候选框和快捷键。拖动测试通过实际 Qt 鼠标事件检查标题栏命中、按钮和正文排除、其他窗口隔离，以及从后台调用切换到 GUI 线程安装事件过滤器；真实 Wayland 桌面是否接受拖动仍需人工确认。

## 2026-10-26 本机验证

KDE Wayland + Fcitx5/Rime，双屏桌面缩放为 100% / 150%。测试窗口使用软件渲染和隔离的应用配置。

- 自带 IBus 插件能加载，但真实输入仍只有英文，说明插件可加载不等于输入服务可用。
- 系统 `/usr/lib/qt/plugins/platforminputcontexts/libfcitx5platforminputcontextplugin.so` 可由应用的 Qt5 加载。加入插件搜索路径后，用户确认候选框和中文输入正常；网页记录到真实 compositionstart/compositionend 和中文提交。
- 去掉临时 `QT_PLUGIN_PATH` 后，修复代码自动找到系统插件，重启复测仍能正常输入中文。单文件打包的冒烟程序也能自动选择 Fcitx 插件并接收中文提交事件。
- 窗口跨屏时网页设备像素比由 1 变为 2。Qt5 在原生 Wayland 下报告整数设备像素比，此记录不代表已经验证了所有桌面的分数缩放。
- Wayland 不支持原有的逐帧设置全局窗口坐标。通过网页异步调用 `startSystemMove()` 也在本机返回失败；改为 Qt 原始鼠标按下事件内调用后，日志确认桌面接受请求，用户确认可以正常拖动窗口。
- 完整 Linux 测试包曾因自带旧 `libstdc++.so.6` 缺少系统 Fcitx 插件所需的 `CXXABI_1.3.15` 而加载失败。打包时排除这份运行库、使用目标系统版本后，普通启动即可加载 Fcitx，用户确认中文输入和拖动正常。该处理已同步到正式 Linux 打包步骤。

参考：[Qt 高 DPI](https://doc.qt.io/qt-6/highdpi.html)、[Fcitx5 Wayland 与 Qt/IBus 兼容说明](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland#QT_IM_MODULE)。
