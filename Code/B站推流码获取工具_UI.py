"""
说明：整合版获取工具

作者：Chace

版本：0.1.1

更新时间：2025-06-24
"""


import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import re
from urllib.parse import unquote
import sys
import requests
import ctypes
from ctypes import wintypes
import webbrowser
import qrcode
from PIL import Image, ImageTk

# 导入原始模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from GetCookies import get_cookies
import data as dt
from update_partition import get_new_partition
from bullet import send_bullet

# 全局变量
code_file = 'code.txt'
cookies_file = 'cookies.txt'
last_settings_file = 'last_settings.json'
my_path = os.getcwd()


class BiliLiveGUI:
    def __init__(self, root):
        self.partition_cat = None
        self.root = root
        self.root.title("B站推流码获取工具")
        # self.root.geometry("900x700")
        self.center_window(900, 700)
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        # 应用图标
        try:
            icon_path = os.path.join(my_path, 'bilibili.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass

        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("微软雅黑", 10))
        self.style.configure("TButton", font=("微软雅黑", 10), padding=5)
        self.style.configure("Header.TLabel", font=("微软雅黑", 16, "bold"), foreground="#00a1d6")
        self.style.configure("Status.TLabel", font=("微软雅黑", 9), foreground="#555")
        self.style.configure("Red.TButton", foreground="red")
        self.style.configure("Green.TButton", foreground="green")
        self.style.configure("TNotebook.Tab", font=("微软雅黑", 10))

        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 创建标题
        self.header = ttk.Label(self.main_frame, text="B站推流码获取工具", style="Header.TLabel")
        self.header.pack(pady=(0, 20))

        # 创建选项卡
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 创建选项卡
        self.setup_tab = ttk.Frame(self.notebook)
        self.live_tab = ttk.Frame(self.notebook)
        self.result_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.setup_tab, text="账号设置")
        self.notebook.add(self.live_tab, text="直播设置")
        self.notebook.add(self.result_tab, text="推流信息")

        # 初始化变量
        self.room_id = tk.StringVar()
        self.cookie_str = tk.StringVar()
        self.csrf = tk.StringVar()
        self.live_title = tk.StringVar(value="我的B站直播")
        self.live_code = tk.StringVar()
        self.live_server = tk.StringVar()

        # 分区数据
        self.partition_data = {}
        self.load_partition_data()
        # self.root.after(0, self.update_partition_ui)
        self.selected_area = tk.StringVar()
        self.selected_sub_area = tk.StringVar()

        # 初始化选项卡
        self.create_setup_tab()
        self.create_live_tab()
        self.create_result_tab()

        self.update_partition_ui()
        self.load_last_settings()

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, style="Status.TLabel", anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)


        # 检查首次运行
        self.check_first_run()
        self.use_cookies_file()

    # 定义一个函数，用于设置窗口居中显示
    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.root.geometry('%dx%d+%d+%d' % (width, height, x, y))

    def get_desktop_folder_path(self):
        """读取注册表，获取桌面路径"""
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, 0x0000, 0, 0, buf)
        return buf.value

    def check_first_run(self):
        """检查是否是首次运行"""
        config_path = os.path.join(my_path, 'config.ini')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as file:
                is_first = file.readline().split(':')[1].strip()
                if int(is_first) == 1:
                    self.show_first_run_info()
                    # 更新配置文件
                    with open(config_path, 'w', encoding='utf-8') as file:
                        file.write('use_first: 0')
        else:
            messagebox.showerror("错误", "未找到config.ini，请尝试重新安装此程序！")

    def show_first_run_info(self):
        """显示首次运行信息"""
        help_path = os.path.join(my_path, '使用说明.txt')
        if os.path.exists(help_path):
            try:
                os.startfile(help_path)
            except:
                messagebox.showinfo("使用说明",
                                    "欢迎使用B站推流码获取工具！\n\n"
                                    "使用步骤：\n"
                                    "1. 在'账号设置'选项卡中设置账号信息\n"
                                    "2. 在'直播设置'选项卡中配置直播参数\n"
                                    "3. 获取推流码并开始直播\n"
                                    "4. 直播结束后点击'停止直播'\n\n"
                                    "详细使用说明：https://download.chacewebsite.cn/uploads/使用说明.txt")
        else:
            messagebox.showinfo("使用说明",
                                "欢迎使用B站推流码获取工具！\n\n"
                                "使用步骤：\n"
                                "1. 在'账号设置'选项卡中设置账号信息\n"
                                "2. 在'直播设置'选项卡中配置直播参数\n"
                                "3. 获取推流码并开始直播\n"
                                "4. 直播结束后点击'停止直播'\n\n"
                                "详细使用说明：https://download.chacewebsite.cn/uploads/使用说明.txt")

    def send_bullet_callback(self):
        """点击发送弹幕按钮时调用"""
        msg = self.bullet_entry.get().strip()
        if not msg:
            messagebox.showwarning("警告", "请输入弹幕内容！")
            return

        if not self.room_id.get() or not self.cookie_str.get() or not self.csrf.get():
            messagebox.showwarning("警告", "请先设置账号信息！")
            return

        # 转换为cookies字典
        cookies_pattern = re.compile(r'(\w+)=([^;]+)(?:;|$)')
        cookies = {key: unquote(value) for key, value in cookies_pattern.findall(self.cookie_str.get())}

        try:
            roomid = int(self.room_id.get())
            csrf = self.csrf.get()

            success, message = send_bullet(msg, csrf, roomid, cookies)

            if success:
                self.log_message(f"弹幕发送成功: {msg}")
                # messagebox.showinfo("成功", f"弹幕发送成功: {message}")
            else:
                self.log_message(f"弹幕发送失败: {message}")
                messagebox.showerror("错误", f"弹幕发送失败: {message}")

            # 清空输入框
            self.bullet_entry.delete(0, tk.END)
        except Exception as e:
            self.log_message(f"发送弹幕时出错: {str(e)}")
            messagebox.showerror("错误", f"发送弹幕时出错:\n{str(e)}")

    def create_setup_tab(self):
        """创建账号设置选项卡"""
        setup_frame = ttk.Frame(self.setup_tab)
        setup_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.setup_tab.grid_rowconfigure(0, weight=1)
        self.setup_tab.grid_columnconfigure(0, weight=1)

        # Cookies文件部分
        file_frame = ttk.LabelFrame(setup_frame, text="Cookies文件")
        file_frame.grid(row=0, column=0, sticky="ew", pady=10)

        ttk.Label(file_frame, text="使用登录记录:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(file_frame, text="使用Cookies文件", command=self.use_cookies_file).grid(row=0, column=1, padx=5,
                                                                                           pady=5)

        # 分隔线
        ttk.Separator(setup_frame, orient="horizontal").grid(row=1, column=0, sticky="ew", pady=10)

        # 自动获取部分
        auto_frame = ttk.LabelFrame(setup_frame, text="自动获取")
        auto_frame.grid(row=2, column=0, sticky="ew", pady=10)

        ttk.Label(auto_frame, text="自动获取账号信息:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(auto_frame, text="自动获取", command=self.auto_get_cookies, style="Green.TButton").grid(
            row=0, column=1, padx=5, pady=5
        )

        # 分隔线
        ttk.Separator(setup_frame, orient="horizontal").grid(row=3, column=0, sticky="ew", pady=10)

        # 手动输入部分
        manual_frame = ttk.LabelFrame(setup_frame, text="手动输入")
        manual_frame.grid(row=4, column=0, sticky="ew", pady=10)

        ttk.Label(manual_frame, text="Room ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        room_entry = ttk.Entry(manual_frame, textvariable=self.room_id, width=40, show='*')
        room_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(manual_frame, text="Cookies:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        cookie_entry = ttk.Entry(manual_frame, textvariable=self.cookie_str, width=40, show='*')
        cookie_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(manual_frame, text="CSRF Token:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        csrf_entry = ttk.Entry(manual_frame, textvariable=self.csrf, width=40, show='*')
        csrf_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(manual_frame, text="保存设置", command=self.save_settings).grid(
            row=3, column=1, padx=5, pady=10, sticky="e"
        )

        # 帮助按钮
        ttk.Button(setup_frame, text="查看使用说明", command=self.show_help).grid(
            row=5, column=0, pady=10, sticky="w"
        )

    def create_live_tab(self):
        """创建直播设置选项卡"""
        live_frame = ttk.Frame(self.live_tab)
        live_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 直播标题
        title_frame = ttk.LabelFrame(live_frame, text="直播标题")
        title_frame.pack(fill=tk.X, pady=10)

        ttk.Label(title_frame, text="请输入直播标题:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.title_entry = ttk.Entry(title_frame, textvariable=self.live_title, width=50)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        # 更新标题按钮
        ttk.Button(title_frame, text="更新标题", command=self.update_title).grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.E
        )

        # 直播分区
        partition_frame = ttk.LabelFrame(live_frame, text="直播分区")
        partition_frame.pack(fill=tk.X, pady=10)

        ttk.Label(partition_frame, text="选择分区:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        # 分区选择下拉框
        self.partition_cat = ttk.Combobox(partition_frame, textvariable=self.selected_area, width=15, state="readonly")
        self.partition_cat.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.partition_cat.bind("<<ComboboxSelected>>", self.update_sub_partitions)

        ttk.Label(partition_frame, text="选择子分区:").grid(row=0, column=2, padx=(20, 5), pady=5, sticky=tk.W)

        self.partition_sub = ttk.Combobox(partition_frame, textvariable=self.selected_sub_area, width=20,
                                          state="readonly")
        self.partition_sub.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        # 更新分区按钮
        ttk.Button(partition_frame, text="更新分区", command=self.update_partition).grid(
            row=0, column=4, padx=5, pady=5, sticky=tk.E
        )

        # 刷新分区按钮
        ttk.Button(partition_frame, text="刷新分区", command=self.refresh_partitions).grid(
            row=0, column=5, padx=10, pady=5
        )

        # 弹幕区域
        bullet_frame = ttk.LabelFrame(live_frame, text="发送弹幕")
        bullet_frame.pack(fill=tk.X, pady=10)

        ttk.Label(bullet_frame, text="输入弹幕内容:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.bullet_entry = ttk.Entry(bullet_frame, width=40)
        self.bullet_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(bullet_frame, text="发送弹幕", command=self.send_bullet_callback).grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.E
        )

        # 开始直播按钮
        btn_frame = ttk.Frame(live_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        self.start_btn = ttk.Button(btn_frame, text="开始直播", command=self.start_live, style="Green.TButton")
        self.start_btn.pack(side=tk.RIGHT, padx=10)

        # 日志区域
        log_frame = ttk.LabelFrame(live_frame, text="操作日志")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.live_log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=8)
        self.live_log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.live_log_area.config(state=tk.DISABLED)

    def create_result_tab(self):
        """创建推流信息选项卡"""
        result_frame = ttk.Frame(self.result_tab)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 推流信息
        info_frame = ttk.LabelFrame(result_frame, text="推流信息")
        info_frame.pack(fill=tk.X, pady=10)

        # 服务器地址
        ttk.Label(info_frame, text="服务器地址:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        server_entry = ttk.Entry(info_frame, textvariable=self.live_server, width=60, state="readonly")
        server_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        # 复制按钮
        ttk.Button(info_frame, text="复制", command=self.copy_server).grid(row=0, column=2, padx=5, pady=5)

        # 推流码
        ttk.Label(info_frame, text="推流码:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        code_entry = ttk.Entry(info_frame, textvariable=self.live_code, width=60, state="readonly")
        code_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # 复制按钮
        ttk.Button(info_frame, text="复制", command=self.copy_code).grid(row=1, column=2, padx=5, pady=5)

        # 导出到文件
        ttk.Button(info_frame, text="导出到桌面", command=self.export_to_desktop).grid(row=2, column=1, padx=5, pady=10,
                                                                                       sticky=tk.E)
        ttk.Button(info_frame, text="另存为...", command=self.export_to_file).grid(row=2, column=2, padx=5, pady=10)

        # 分隔线
        ttk.Separator(result_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)

        # 操作按钮
        btn_frame = ttk.Frame(result_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.stop_btn = ttk.Button(btn_frame, text="停止直播", command=self.stop_live, style="Red.TButton",
                                   state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=10)

        # 日志区域
        log_frame = ttk.LabelFrame(result_frame, text="操作日志")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=8)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area.config(state=tk.DISABLED)

    def show_qr_code(self, qr_url):
        """生成并显示二维码"""
        # 创建新窗口
        qr_window = tk.Toplevel(self.root)
        qr_window.title("人脸认证二维码")
        # qr_window.geometry("400x450")
        width = 400
        height = 450

        screen_width = qr_window.winfo_screenwidth()
        screen_height = qr_window.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        qr_window.geometry('%dx%d+%d+%d' % (width, height, x, y))

        qr_window.resizable(False, False)

        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为Tkinter可用的图像
        img_tk = ImageTk.PhotoImage(img)

        # 显示二维码
        label = tk.Label(qr_window, image=img_tk)
        label.image = img_tk  # 保持引用，避免被垃圾回收
        label.pack(pady=10)

        # 添加提示文字
        tk.Label(
            qr_window,
            text="请使用B站客户端扫描二维码完成人脸认证",
            font=("微软雅黑", 10)
        ).pack(pady=10)

        def close_qr_window():
            qr_window.destroy()
            self.log_message("已进行人脸认证！")

        # 添加关闭按钮
        tk.Button(
            qr_window,
            text="关闭",
            command=close_qr_window,
            width=15
        ).pack(pady=10)

    def log_message(self, message):
        """记录日志消息，并同步更新所有日志区域"""
        # 更新主日志区域（推流信息页）
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

        # 更新直播设置页的日志区域（如果存在）
        if hasattr(self, 'live_log_area'):
            self.live_log_area.config(state=tk.NORMAL)
            self.live_log_area.insert(tk.END, message + "\n")
            self.live_log_area.see(tk.END)
            self.live_log_area.config(state=tk.DISABLED)

        # 更新状态栏
        self.status_var.set(message)

    def show_help(self):
        """显示使用说明"""
        help_path = os.path.join(my_path, '使用说明.txt')
        if os.path.exists(help_path):
            try:
                os.startfile(help_path)
            except:
                webbrowser.open('https://download.chacewebsite.cn/uploads/使用说明.txt')
        else:
            webbrowser.open('https://download.chacewebsite.cn/uploads/使用说明.txt')

    def save_last_settings(self):
        """保存最后一次使用的标题和分区信息"""
        settings = {
            "live_title": self.live_title.get(),
            "selected_area": self.selected_area.get(),
            "selected_sub_area": self.selected_sub_area.get()
        }
        file_path = os.path.join(my_path, last_settings_file)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.log_message(f"保存上次设置失败: {str(e)}")

    def load_last_settings(self):
        """加载上次使用的标题和分区信息"""
        file_path = os.path.join(my_path, last_settings_file)
        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # 恢复标题
            if settings.get("live_title"):
                self.live_title.set(settings["live_title"])

            # 恢复分区选择
            if settings.get("selected_area") and settings.get("selected_sub_area"):
                self.selected_area.set(settings["selected_area"])
                self.update_sub_partitions()  # 更新子分区下拉框
                self.selected_sub_area.set(settings["selected_sub_area"])
        except Exception as e:
            self.log_message(f"加载上次设置失败: {str(e)}")

    def update_title(self):
        """手动更新直播标题"""
        if not self.room_id.get() or not self.cookie_str.get() or not self.csrf.get():
            messagebox.showwarning("警告", "请先设置账号信息！")
            return

        if not self.live_title.get():
            messagebox.showwarning("警告", "请填写直播标题！")
            return

        self.log_message("正在更新直播标题...")
        threading.Thread(target=self._update_title_thread, daemon=True).start()

    def _update_title_thread(self):
        try:
            # 准备请求参数
            header = dt.header
            data = dt.title_data.copy()
            data['room_id'] = self.room_id.get()
            data['csrf_token'] = data['csrf'] = self.csrf.get()
            data['title'] = self.live_title.get()

            # 转换为cookies字典
            cookies_pattern = re.compile(r'(\w+)=([^;]+)(?:;|$)')
            cookies = {key: unquote(value) for key, value in cookies_pattern.findall(self.cookie_str.get())}

            # 发送设置标题请求
            response = requests.post(
                'https://api.live.bilibili.com/room/v1/Room/update',
                cookies=cookies,
                headers=header,
                data=data
            )

            if response.status_code != 200 or response.json()['code'] != 0:
                raise Exception(f"设置标题失败: {response.json()}")

            self.root.after(0, lambda: messagebox.showinfo("成功", "直播标题已更新！"))
            self.log_message("直播标题已更新！")
            self.save_last_settings()
        except Exception as e:
            self.log_message(f"更新直播标题时出错: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"更新直播标题时出错:\n{str(e)}"))

    def update_partition(self):
        """手动更新直播分区"""
        area_id = self.get_selected_area_id()
        if not area_id:
            messagebox.showwarning("警告", "请选择有效的直播分区！")
            return

        if not self.room_id.get() or not self.cookie_str.get() or not self.csrf.get():
            messagebox.showwarning("警告", "请先设置账号信息！")
            return

        self.log_message("正在更新直播分区...")
        threading.Thread(target=self._update_partition_thread, args=(area_id,), daemon=True).start()

    def _update_partition_thread(self, area_id):
        try:
            # 准备请求参数
            header = dt.header
            data = dt.id_data.copy()
            data['room_id'] = self.room_id.get()
            data['csrf_token'] = data['csrf'] = self.csrf.get()
            data['area_id'] = area_id

            # 转换为cookies字典
            cookies_pattern = re.compile(r'(\w+)=([^;]+)(?:;|$)')
            cookies = {key: unquote(value) for key, value in cookies_pattern.findall(self.cookie_str.get())}

            # 发送更新分区请求
            response = requests.post(
                'https://api.live.bilibili.com/room/v1/Room/update',
                cookies=cookies,
                headers=header,
                data=data
            )

            if response.status_code != 200 or response.json()['code'] != 0:
                raise Exception(f"更新分区失败: {response.json()}")

            self.log_message("直播分区已更新！")
            self.root.after(0, lambda: messagebox.showinfo("成功", "直播分区已更新！"))
            self.save_last_settings()
        except Exception as e:
            self.log_message(f"更新直播分区时出错: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"更新直播分区时出错:\n{str(e)}"))

    def use_cookies_file(self):
        """使用cookies.txt文件"""
        cookies_path = os.path.join(my_path, cookies_file)
        if os.path.exists(cookies_path):
            try:
                with open(cookies_path, 'r', encoding='utf-8') as file:
                    value = []
                    for line in file:
                        if line.strip():
                            value.append(line.split(':')[1].strip())

                    if len(value) >= 3:
                        self.room_id.set(value[0])
                        self.cookie_str.set(value[1])
                        self.csrf.set(value[2])
                        self.log_message("成功加载cookies.txt文件")
                        messagebox.showinfo("成功", "Cookies文件加载成功！")
                        self.notebook.select(self.live_tab)
                        self.root.focus_force()
                        # self.root.after(0, lambda: self.partition_cat.focus())
                    else:
                        messagebox.showerror("错误", "cookies.txt文件格式不正确")
            except Exception as e:
                self.log_message(f"打开或读取cookies.txt文件时出错: {str(e)}")
                messagebox.showerror("错误", f"打开或读取cookies.txt文件时出错:\n{str(e)}")
        else:
            messagebox.showwarning("警告", f"未找到{cookies_file}文件")

    def auto_get_cookies(self):
        """自动获取cookies"""
        self.log_message("开始自动获取账号信息...")
        # 在新线程中执行获取cookies的操作
        threading.Thread(target=self._auto_get_cookies_thread, daemon=True).start()

    def _auto_get_cookies_thread(self):
        try:
            room_id, cookie_str, csrf = get_cookies()
            self.room_id.set(room_id)
            self.cookie_str.set(cookie_str)
            self.csrf.set(csrf)
            self.log_message("账号信息获取成功！")
            messagebox.showinfo("成功", "账号信息获取成功！")
            self.save_settings()
        except Exception as e:
            self.log_message(f"获取账号信息出错: {str(e)}")
            messagebox.showerror("错误", f"获取账号信息出错: {str(e)}")

    def save_settings(self):
        """保存设置到cookies.txt"""
        if not self.room_id.get() or not self.cookie_str.get() or not self.csrf.get():
            messagebox.showwarning("警告", "请填写所有字段！")
            return

        try:
            cookies_path = os.path.join(my_path, cookies_file)
            with open(cookies_path, 'w', encoding='utf-8') as file:
                file.write('room_id:' + str(self.room_id.get()) + '\n\n\n')
                file.write('cookie:' + str(self.cookie_str.get()) + '\n\n\n')
                file.write('csrf:' + str(self.csrf.get()) + '\n')

            self.log_message("账号信息保存成功！")
            messagebox.showinfo("成功", "账号信息保存成功！")
            self.notebook.select(self.live_tab)
        except Exception as e:
            self.log_message(f"保存设置时出错: {str(e)}")
            messagebox.showerror("错误", f"保存设置时出错:\n{str(e)}")

    def refresh_partitions(self):
        """刷新直播分区"""
        if not self.cookie_str.get():
            messagebox.showwarning("警告", "请先设置账号信息！")
            return

        # 转换为cookies字典
        cookies_pattern = re.compile(r'(\w+)=([^;]+)(?:;|$)')
        cookies = {key: unquote(value) for key, value in cookies_pattern.findall(self.cookie_str.get())}

        self.log_message("正在获取直播分区...")
        threading.Thread(target=self._refresh_partitions_thread, args=(cookies,), daemon=True).start()

    def load_partition_data(self):
        """从 partition.json 加载分区数据"""
        json_path = os.path.join(my_path, 'partition.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)["data"]

            self.partition_data = {}
            for category in raw_data:
                cat_name = category['name']
                sub_areas = {}
                for item in category.get('list', []):
                    sub_areas[item['id']] = item['name']
                self.partition_data[cat_name] = sub_areas
        except Exception as e:
            messagebox.showerror("错误", f"加载分区数据失败: {str(e)}")

    def _refresh_partitions_thread(self, cookies):
        try:
            get_new_partition(cookies)

            self.load_partition_data()

            # 更新分区下拉框
            self.root.after(0, self.update_partition_ui)

            self.log_message("直播分区获取成功！")
        except Exception as e:
            self.log_message(f"获取直播分区失败: {str(e)}")
            messagebox.showerror("错误", f"获取直播分区失败:\n{str(e)}")

    def update_partition_ui(self):
        """更新一级分区UI"""
        if self.partition_data:
            main_areas = list(self.partition_data.keys())
            self.partition_cat['values'] = main_areas
            if main_areas:
                self.selected_area.set(main_areas[0])
                self.update_sub_partitions()

    def update_sub_partitions(self, event=None):
        """更新子分区选项"""
        main_area_name = self.selected_area.get()
        if not main_area_name:
            return

        sub_areas_dict = self.partition_data.get(main_area_name, {})
        sub_areas = list(sub_areas_dict.values())

        self.partition_sub['values'] = sub_areas
        if sub_areas:
            self.selected_sub_area.set(sub_areas[0])

    def get_selected_area_id(self):
        """获取选中的分区ID"""
        main_area_name = self.selected_area.get()
        sub_area_name = self.selected_sub_area.get()

        if main_area_name and sub_area_name and main_area_name in self.partition_data:
            for area_id, area_name in self.partition_data[main_area_name].items():
                if area_name == sub_area_name:
                    return area_id
        return None

    def start_live(self):
        """开始直播"""
        if not self.room_id.get() or not self.cookie_str.get() or not self.csrf.get():
            messagebox.showwarning("警告", "请先设置账号信息！")
            return

        if not self.live_title.get():
            messagebox.showwarning("警告", "请设置直播标题！")
            return

        area_id = self.get_selected_area_id()
        if not area_id:
            messagebox.showwarning("警告", "请选择直播分区！")
            return

        if self.live_server.get() or self.live_code.get():
            messagebox.showwarning("警告", "正在进行直播！")
            return

        self.log_message("正在开始直播...")
        self.start_btn.config(state=tk.DISABLED)

        # 在新线程中执行开始直播的操作
        threading.Thread(target=self._start_live_thread, args=(area_id,), daemon=True).start()

        self.save_last_settings()

    def _start_live_thread(self, area_id):
        try:
            # 准备请求参数
            header = dt.header
            data = dt.start_data.copy()
            data['room_id'] = self.room_id.get()
            data['csrf_token'] = data['csrf'] = self.csrf.get()
            data['area_v2'] = area_id

            # 转换为cookies字典
            cookies_pattern = re.compile(r'(\w+)=([^;]+)(?:;|$)')
            cookies = {key: unquote(value) for key, value in cookies_pattern.findall(self.cookie_str.get())}

            # 设置直播标题
            title_data = dt.title_data.copy()
            title_data['room_id'] = self.room_id.get()
            title_data['csrf_token'] = title_data['csrf'] = self.csrf.get()
            title_data['title'] = self.live_title.get()

            # 发送设置标题请求
            title_response = requests.post(
                'https://api.live.bilibili.com/room/v1/Room/update',
                cookies=cookies,
                headers=header,
                data=title_data
            )

            if title_response.status_code != 200 or title_response.json()['code'] != 0:
                self.log_message(f"设置直播标题失败: {title_response.json()}")
                messagebox.showerror("错误", "设置直播标题失败！")
                return

            self.log_message("直播标题设置成功")

            # 获取推流码
            self.log_message("正在获取直播推流码...")
            response = requests.post(
                'https://api.live.bilibili.com/room/v1/Room/startLive',
                cookies=cookies,
                headers=header,
                data=data
            )

            if response.status_code != 200 or response.json()['code'] != 0:
                if response.json()['code'] == 60024:
                    self.log_message("获取推流码失败: 需要进行人脸认证")
                    qr: str = response.json()['data']['qr']

                    # 生成二维码并显示
                    self.root.after(0, lambda: self.show_qr_code(qr))

                else:
                    self.log_message(f"获取推流码失败: {response.json()}")
                    messagebox.showerror("错误", "获取推流码失败，cookie可能已失效！")

                    # 删除cookies文件
                    cookies_path = os.path.join(my_path, cookies_file)
                    if os.path.exists(cookies_path):
                        try:
                            os.remove(cookies_path)
                            self.log_message("已删除失效的cookies.txt文件")
                        except Exception as e:
                            self.log_message(f"删除cookies.txt文件时出错: {str(e)}")

                return

            # 获取推流信息
            rtmp_addr = response.json()['data']['rtmp']['addr']
            rtmp_code = response.json()['data']['rtmp']['code']

            # 更新UI
            self.root.after(0, lambda: self._update_after_start(rtmp_addr, rtmp_code))

            self.log_message("直播已开启！请使用推流码进行直播")
            messagebox.showinfo("成功", "直播已开启！请使用推流码进行直播")

        except Exception as e:
            self.log_message(f"开始直播时出错: {str(e)}")
            messagebox.showerror("错误", f"开始直播时出错:\n{str(e)}")
        finally:
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))

    def _update_after_start(self, rtmp_addr, rtmp_code):
        """开始直播后更新UI"""
        self.live_server.set(rtmp_addr)
        self.live_code.set(rtmp_code)
        self.stop_btn.config(state=tk.NORMAL)
        # self.live_status.config(text="直播已开启", foreground="green")
        self.notebook.select(self.result_tab)

    def stop_live(self):
        """停止直播"""
        if not self.live_server.get() or not self.live_code.get():
            messagebox.showwarning("警告", "没有正在进行的直播！")
            return

        self.log_message("正在停止直播...")
        self.stop_btn.config(state=tk.DISABLED)

        # 在新线程中执行停止直播的操作
        threading.Thread(target=self._stop_live_thread, daemon=True).start()

    def _stop_live_thread(self):
        try:
            # 准备请求参数
            header = dt.header
            data = dt.stop_data.copy()
            data['room_id'] = self.room_id.get()
            data['csrf_token'] = data['csrf'] = self.csrf.get()

            # 转换为cookies字典
            cookies_pattern = re.compile(r'(\w+)=([^;]+)(?:;|$)')
            cookies = {key: unquote(value) for key, value in cookies_pattern.findall(self.cookie_str.get())}

            # 发送停止直播请求
            response = requests.post(
                'https://api.live.bilibili.com/room/v1/Room/stopLive',
                cookies=cookies,
                headers=header,
                data=data
            )

            if response.status_code != 200 or response.json()['code'] != 0:
                self.log_message(f"停止直播失败: {response.json()}")
                messagebox.showerror("错误", "停止直播失败！")
                return

            # 更新UI
            self.root.after(0, self._update_after_stop)

            self.log_message("直播已停止！")
            messagebox.showinfo("成功", "直播已停止！")

        except Exception as e:
            self.log_message(f"停止直播时出错: {str(e)}")
            messagebox.showerror("错误", f"停止直播时出错:\n{str(e)}")
        finally:
            self.root.after(0, lambda: self.stop_btn.config(state=tk.NORMAL))

    def _update_after_stop(self):
        """停止直播后更新UI"""
        self.live_server.set("")
        self.live_code.set("")
        # self.live_status.config(text="直播已停止", foreground="red")
        self.notebook.select(self.live_tab)

    def copy_server(self):
        """复制服务器地址"""
        if self.live_server.get():
            self.root.clipboard_clear()
            self.root.clipboard_append(self.live_server.get())
            self.log_message("已复制服务器地址到剪贴板")

    def copy_code(self):
        """复制推流码"""
        if self.live_code.get():
            self.root.clipboard_clear()
            self.root.clipboard_append(self.live_code.get())
            self.log_message("已复制推流码到剪贴板")

    def export_to_desktop(self):
        """导出推流码到桌面"""
        if not self.live_server.get() or not self.live_code.get():
            messagebox.showwarning("警告", "没有可导出的推流信息！")
            return

        try:
            desktop = self.get_desktop_folder_path()
            file_path = os.path.join(desktop, code_file)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"服务器地址: {self.live_server.get()}\n")
                f.write(f"推流码: {self.live_code.get()}\n")

            self.log_message(f"推流信息已保存到桌面: {file_path}")
            messagebox.showinfo("成功", f"推流信息已保存到桌面:\n{file_path}")

            # 打开文件
            try:
                os.startfile(file_path)
            except:
                pass

        except Exception as e:
            self.log_message(f"保存文件出错: {str(e)}")
            messagebox.showerror("错误", f"保存文件出错:\n{str(e)}")

    def export_to_file(self):
        """导出推流码到指定文件"""
        if not self.live_server.get() or not self.live_code.get():
            messagebox.showwarning("警告", "没有可导出的推流信息！")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="保存推流信息"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"服务器地址: {self.live_server.get()}\n")
                    f.write(f"推流码: {self.live_code.get()}\n")
                self.log_message(f"推流信息已保存到: {file_path}")
                messagebox.showinfo("成功", f"推流信息已保存到:\n{file_path}")
            except Exception as e:
                self.log_message(f"保存文件出错: {str(e)}")
                messagebox.showerror("错误", f"保存文件出错:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BiliLiveGUI(root)
    root.mainloop()