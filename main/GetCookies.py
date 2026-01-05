"""
说明：一个用于获取登录二维码和cookies的文档

作者：Chace

版本：1.1.1

更新时间：2025-11-04

常用函数：

1. get_qrcode() -> dict

2. qr_login(qrcode_key: str) -> requests.Response

3. login(qr_string: str, qrcode_key: str) -> dict

4. get_cookies() -> tuple
"""

import io
import requests
import data as dt
import time
import qrcode
import json
import tkinter
import tkinter as tk
from util import center_window

def get_qrcode() -> dict:
    """
    生成登录二维码的URL和key

    :return: 二维码相关数据
    """
    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    headers = {'User-Agent': dt.user_agent}
    response = requests.get(url, headers=headers)
    return response.json()["data"]


def qr_login(qrcode_key: str) -> requests.Response:
    """
    访问Bilibili服务器检查二维码扫描后的登录状态
    :param qrcode_key: 二维码秘钥
    :return: 返回查询响应
    """
    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    headers = {'User-Agent': dt.user_agent}
    params = {'qrcode_key': qrcode_key}
    response = requests.get(url, headers=headers, params=params)
    return response


def get_qr() -> tuple:
    """
    生成二维码字符串，与秘钥一同返回
    :return: 一个元组，按顺序包含二维码字符串和秘钥
    """
    data = get_qrcode()  # 获取二维码数据
    qrcode_url = data["url"]
    qrcode_key = data["qrcode_key"]

    # 显示二维码URL并生成文本二维码
    output = io.StringIO()
    qr = qrcode.QRCode()
    qr.add_data(qrcode_url)
    qr.print_ascii(out=output, tty=False, invert=False)
    qr_string = output.getvalue()

    return qr_string, qrcode_key


def login(qr_string: str, qrcode_key: str) -> dict:
    """
    登录，获取cookies
    :param qr_string: 二维码字符串
    :param qrcode_key: 二维码秘钥
    :return: 返回cookies，获取失败返回None
    """
    print(qr_string)

    print("请扫描二维码进行登录")

    cookies = None
    while not cookies:  # 等待用户扫描并登录
        try:
            login_requests = qr_login(qrcode_key)
            login_data = login_requests.json()
        except Exception:
            raise ConnectionError("登录连接错误！")
        else:
            code = login_data["data"]["code"]

            if code == 0:
                cookies = login_requests.cookies.get_dict()
                break
            elif code == 86038:
                print("\n二维码已失效，请重新生成")
            elif code == 86090:
                print("\n二维码已扫描，等待确认")

        time.sleep(1.5)  # 每1.5秒轮询一次

    return cookies


def get_room_id_and_csrf(cookies: dict) -> tuple:
    """
    获取room_id和csrf
    :param cookies: cookies
    :return: 一个元组，按顺序包含room_id和csrf
    """
    room_id = None
    csrf = None

    dede_user_id = cookies.get("DedeUserID")
    url = f"https://api.live.bilibili.com/room/v2/Room/room_id_by_uid?uid={dede_user_id}"

    try:
        response = requests.get(url, headers={'User-Agent': dt.user_agent})
        data = response.json()
    except Exception:
        raise ConnectionError("获取room_id失败！")
    else:
        if data['code'] == 0:
            room_id = data['data']['room_id']

    csrf = cookies.get("bili_jct")

    return room_id, csrf

def login_enter(windows: tkinter.Tk, qrcode_key: str, c_list: list, login_label: tkinter.Label, is_login: bool) -> None:
    """
    获取到登录二维码后，轮序检测是否登录成功
    :param windows: 回调函数所绑定的窗口
    :param qrcode_key: 二维码秘钥
    :param c_list: 存储cookies
    :param login_label: 登录状态的标签
    :param is_login: 是否登录成功或失效
    :return: None
    """
    if not is_login:
        try:
            login_requests = qr_login(qrcode_key)
            login_data = login_requests.json()
        except Exception:
            raise ConnectionError("登录连接错误！")
        else:
            code = login_data["data"]["code"]

            if code == 0:
                c_list[0] = login_requests.cookies.get_dict()
                windows.destroy()
                is_login = True
            elif code == 86038:
                login_label.config(text="\n二维码已失效，请重新启动软件")
                windows.destroy()
                is_login = True
            elif code == 86090:
                login_label.config(text="\n二维码已扫描，等待确认")
        windows.after(1000, login_enter, windows, qrcode_key, c_list, login_label, is_login)


def login_ui() -> dict | None:
    """
    扫码登录窗口
    :return: 登录失败返回None，否则返回cookies
    """
    window = tk.Tk()
    center_window(window, 600, 550)
    # 设置统一宽度的字体
    import platform
    system = platform.system()
    if system == 'Linux':
        label_font = ('DejaVu Sans Mono', 12)
    else:
        label_font = ('Courier New', 12)
    window.title('B站推流码获取工具')
    qr_str, qr_key = get_qr()
    cookies_list = [None]
    login_label = tk.Label(window, text='\n扫描二维码登录 ', anchor='center', font=label_font)
    login_label.pack()
    tk.Label(window, text=qr_str, anchor='center', font=label_font).pack()
    login_enter(window, qr_key, cookies_list, login_label, False)

    # 使窗口避免被遮挡，并且获取焦点
    window.attributes('-topmost', True)
    window.bind("<FocusIn>", lambda event: window.attributes('-topmost', False))

    window.mainloop()
    return cookies_list[0]


def get_cookies() -> tuple:
    """
    完全获取room_id、cookies和csrf
    :return: 一个元组，按顺序包含room_id、cookies（字符串形式）和csrf
    """
    room_id = None
    cookies_str = None
    csrf = None

    cookies = login_ui()

    if cookies:
        room_id, csrf = get_room_id_and_csrf(cookies)
        cookies_str = json.dumps(cookies, separators=(';', '='), ensure_ascii=False).replace('{', '').replace('}',
                                                                                                              '').replace(
            r'"', '')
    return room_id, cookies_str, csrf


if __name__ == '__main__':
    print(get_cookies())
