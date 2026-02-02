import hashlib
import urllib.parse
import requests
import logging
from backend import data as dt

# 配置模块日志
logger = logging.getLogger("BiliAPI")


class BilibiliApi:
    # B站直播姬 App Key
    APP_KEY = "aae92bc66f3edfab"
    APP_SEC = "af125a0d5279fd576c1b4418a3e8276d"

    def __init__(self):
        self.cookies = {}
        self.headers = dt.header.copy()

    def update_cookies(self, cookies: dict):
        self.cookies = cookies

    def _appsign(self, params: dict) -> dict:
        """为请求参数进行 APP 签名"""
        params.update({'appkey': self.APP_KEY})
        params = dict(sorted(params.items()))
        query = urllib.parse.urlencode(params)
        sign = hashlib.md5((query + self.APP_SEC).encode()).hexdigest()
        params.update({'sign': sign})
        return params

    def _req(self, method, url, params=None, data=None):
        """通用请求封装"""
        try:
            if method == "GET":
                resp = requests.get(url, params=params, cookies=self.cookies, headers=self.headers, timeout=10)
            else:
                resp = requests.post(url, params=params, data=data, cookies=self.cookies, headers=self.headers,
                                     timeout=10)

            # 尝试解析 JSON
            try:
                json_data = resp.json()
                return True, json_data
            except ValueError:
                logger.error(f"JSON Decode Error. Status: {resp.status_code}, Content: {resp.text[:100]}")
                return False, {"code": -1, "msg": "API 返回格式错误"}

        except Exception as e:
            logger.error(f"Request Error: {url} -> {e}")
            return False, {"code": -1, "msg": str(e)}

    # --- 扫码登录 ---
    def get_passport_qrcode(self):
        return self._req("GET", "https://passport.bilibili.com/x/passport-login/web/qrcode/generate")

    def poll_passport_qrcode(self, qrcode_key):
        try:
            url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
            params = {"qrcode_key": qrcode_key}
            resp = requests.get(url, params=params, headers=self.headers, timeout=10)
            return True, resp.json(), resp.cookies.get_dict()
        except Exception as e:
            return False, {"code": -1, "msg": str(e)}, {}

    # --- 用户信息 ---
    def get_user_info(self):
        """获取基本信息 (昵称、等级、头像、硬币等)"""
        return self._req("GET", "https://api.bilibili.com/x/web-interface/nav")

    def get_user_stat(self):
        """[新增] 获取统计信息 (粉丝数、关注数、动态数)"""
        return self._req("GET", "https://api.bilibili.com/x/web-interface/nav/stat")

    def get_room_id_by_uid(self, uid):
        """通过 UID 获取直播间 ID"""
        return self._req("GET", f"https://api.live.bilibili.com/room/v2/Room/room_id_by_uid?uid={uid}")

    # --- 直播控制 ---
    def get_area_list(self):
        return self._req("GET", "https://api.live.bilibili.com/room/v1/Area/getList", params={"show_pinyin": 1})

    def update_title(self, room_id, title, csrf):
        data = {'room_id': room_id, 'platform': 'pc_link', 'title': title, 'csrf_token': csrf, 'csrf': csrf}
        return self._req("POST", "https://api.live.bilibili.com/room/v1/Room/update", data=data)

    def update_area(self, room_id, area_id, csrf):
        data = {'room_id': room_id, 'area_id': area_id, 'platform': 'pc_link', 'csrf_token': csrf, 'csrf': csrf}
        return self._req("POST", "https://api.live.bilibili.com/room/v1/Room/update", data=data)

    def start_live(self, room_id, area_id, csrf):
        # 1. 获取时间戳
        s1, t_resp = self._req("GET", "https://api.bilibili.com/x/report/click/now")
        if not s1 or t_resp['code'] != 0: return False, t_resp
        ts = t_resp["data"]["now"]

        # 2. 获取版本
        v_params = self._appsign({"system_version": 2, "ts": ts})
        s2, v_resp = self._req("GET",
                               "https://api.live.bilibili.com/xlive/app-blink/v1/liveVersionInfo/getHomePageLiveVersion",
                               params=v_params)
        if not s2 or v_resp['code'] != 0: return False, v_resp

        # 3. 开始直播
        data = {
            'room_id': room_id, 'platform': 'pc_link', 'area_v2': area_id, 'backup_stream': '0',
            'csrf_token': csrf, 'csrf': csrf, 'build': v_resp['data']['build'],
            'version': v_resp['data']['curr_version'], 'ts': ts
        }
        return self._req("POST", "https://api.live.bilibili.com/room/v1/Room/startLive", data=self._appsign(data))

    def stop_live(self, room_id, csrf):
        data = {'room_id': room_id, 'platform': 'pc_link', 'csrf_token': csrf, 'csrf': csrf}
        return self._req("POST", "https://api.live.bilibili.com/room/v1/Room/stopLive", data=data)