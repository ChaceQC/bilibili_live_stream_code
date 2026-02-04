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

### 环境要求

- **Python**: 3.9+
- **Node.js**: 18+

### 构建步骤

1. **克隆仓库**

   ```bash
   git clone https://github.com/your-repo/bilibili_live_stream_code.git
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
     pyinstaller main.py --name BiliLiveTool --onefile --add-data "frontend/dist:frontend/dist" --icon "bilibili.icns" --windowed
     ```

   - **Linux**:
     ```bash
     pyinstaller main.py --name BiliLiveTool --onefile --add-data "frontend/dist:frontend/dist" --icon "bilibili.png"
     ```

6. **运行**

   构建完成后，可执行文件位于 `dist` 目录下。

## 其他

1. 支持推流码类型：RTMP和SRT；
