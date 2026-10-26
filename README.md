# 哔哩哔哩直播工具

1. 用于在准备直播时获取第三方推流码，以便可以绕开哔哩哔哩直播姬，直接在如OBS等软件中进行直播；
2. 支持开播时定义标题和分区；
3. 支持弹幕监控（含进场消息和礼物消息）以及发送弹幕；

## 声明

**本程序仅用于学习和交流，禁止用于商业或其他目的，任何不当使用导致的问题自行负责。*

## 使用教程

1. 扫码登录B站账号；
2. 填写标题并选择分区（首次使用需要点击`同步`）；
3. 点击 `开始直播` 来开始直播；
4. 在 *推流码* 复制链接和推流码至第三方推流工具；
5. 在 *弹幕* 界面，可以查看并发送弹幕；
6. 点击 `停止直播` 或关闭软件来停止直播，**使用 OBS 的 `停止直播` 并不会停止直播**；

## 自行构建

### macOS 下载

- Apple Silicon（M1/M2/M3/M4 等 M 系列）请选择 `macos-arm64.zip`；Intel Mac 请选择 `macos-amd64.zip`。
- arm64 版本在原生 Apple Silicon runner 上打包，并检查可执行文件架构和应用签名完整性。

### 环境要求

- **Python**: 3.9+
- **Node.js**: 18+

### 构建步骤

1. **克隆仓库**

   ```bash
   git clone https://github.com/ChaceQC/bilibili_live_stream_code.git
   cd bilibili_live_stream_code
   ```

2. **构建前端**

   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

3. **安装后端依赖**

   ```bash
   pip install -r requirements.txt
   pip install pyinstaller Pillow
   ```

   **Linux**：无需额外系统依赖，程序使用内置的 Qt 库运行托盘。建议在 Ubuntu 20.04+ 或其他主流发行版上运行。
   
   > 若启动时提示 `Qt platform plugin "xcb" could not be found`，请安装：  
   > `sudo apt install libxcb-xinerama0 libxcb-cursor0 libnss3`

   Linux 的 Qt5 后端默认启用高 DPI 缩放，跟随桌面设置，无需固定为 200%。已有的 `QT_ENABLE_HIGHDPI_SCALING`、`QT_SCALE_FACTOR` 设置会保留。

   Wayland 下按住顶部标题栏空白处即可拖动窗口。程序在 Qt 原始鼠标事件中请求桌面系统移动窗口，右上角窗口按钮不属于拖动区域。

   使用 Fcitx5 时，若设置了 `QT_IM_MODULE=fcitx`，程序会优先使用当前 Qt 的 Fcitx 插件，缺失时查找常见系统 Qt 插件目录，并验证插件能否加载。可通过系统软件包安装 Qt5 的 Fcitx 输入法插件，或通过 `QT_PLUGIN_PATH` 指定自定义插件目录。只有找不到可加载的 Fcitx 插件时才尝试 IBus 回退；这需要 Fcitx5 的 IBus 前端启用且能被 Qt 连接，不能保证在所有桌面环境生效。其他输入法设置保持不变。

   从源码运行时还需 pip 安装：
   ```bash
   pip install PyGObject
   ```

   > 未安装时程序仍可正常运行，仅无托盘图标。打包后的二进制仅需系统包（无需 pip 安装）。

4. **准备图标 (可选)**

   - **macOS (ico -> icns)**:
     ```bash
     # 使用 sips 和 iconutil (macOS 自带)
     sips -s format png bilibili.ico --out temp_icon.png
     mkdir bilibili.iconset
     sips -z 1024 1024 temp_icon.png --out bilibili.iconset/icon_512x512@2x.png
     iconutil -c icns bilibili.iconset
     rm -rf bilibili.iconset temp_icon.png
     ```

   - **Linux (ico -> png)**:
     ```bash
     # 使用 Python Pillow 库
     python -c "from PIL import Image; Image.open('bilibili.ico').save('bilibili.png')"
     ```

5. **打包应用**

   - **Windows**:
     ```bash
     pyinstaller main.py --name BiliLiveTool --onefile --add-data "frontend/dist;frontend/dist" --icon "bilibili.ico" --noconsole
     ```

   - **macOS**:
     ```bash
     pyinstaller main.py --name BiliLiveTool --onedir --add-data "frontend/dist:frontend/dist" --icon "bilibili.icns" --hidden-import _cffi_backend --windowed
     ```

     macOS 使用目录打包模式，避免再次打开应用时单文件启动器产生额外 Dock 图标；在 Finder 中仍显示为一个 `.app` 应用。
     使用 `7z` 压缩 macOS 应用时需添加 `-snl` 保留符号链接，确保 Qt 框架结构和签名完整。

   - **Linux**:
     ```bash
     pyinstaller main.py --name BiliLiveTool --onefile \
      --add-data "frontend/dist:frontend/dist" \
      --add-data "bilibili.ico:." \
      --icon "bilibili.png" \
      --hidden-import _cffi_backend \
      --hidden-import cffi \
      --hidden-import qtpy \
      --hidden-import PyQt5 \
      --hidden-import webview.platforms.qt
     ```

6. **运行**

   构建完成后，可执行文件位于 `dist` 目录下。

## 其他

1. 支持推流码类型：RTMP和SRT；
2. 因为本人穷，用不起mac，mac用户可以自行进行测试，如果调试到可以正常运行，欢迎提交pr；
3. 社区已有基于本项目的 Tauri 重构版本，技术栈从 Python + PyInstaller 迁移至 **Tauri 2.x (Rust) + React 18 + TypeScript**，并补全了 macOS 端的适配（含托盘、窗口退出、深色模式等）。有需要的同学可以移步 [Zeppelinpp/bilibili-streamer](https://github.com/Zeppelinpp/bilibili-streamer) 查看。

### ⭐ Star 历史

   [![Stargazers over time](https://starchart.cc/ChaceQC/bilibili_live_stream_code.svg?variant=adaptive)](https://starchart.cc/ChaceQC/bilibili_live_stream_code)
