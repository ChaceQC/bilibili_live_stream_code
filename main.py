import os
import sys
import webview
import logging
import json
from backend.bilibili_api import BilibiliApi
from backend import util

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Main")


# 获取程序路径
def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


CONFIG_FILE = os.path.join(get_app_path(), "config.json")


class Api:
    def __init__(self):
        self.api = BilibiliApi()
        self.partition_map = {}
        self.current_area_id = None
        self.current_area_names = []
        self.is_maximized = False
        self.config = self._load_config()
        self.room_id = ""
        self.csrf = ""
        self._init_current_user()

    # --- 窗口控制接口 ---

    def window_min(self):
        """最小化"""
        webview.windows[0].minimize()

    def window_max(self):
        """最大化/还原切换"""
        window = webview.windows[0]
        if self.is_maximized:
            window.restore()
            self.is_maximized = False
        else:
            window.maximize()
            self.is_maximized = True
        return {"code": 0, "is_maximized": self.is_maximized}

    def window_close(self):
        """关闭程序"""
        self._save_config()
        webview.windows[0].destroy()

    def get_window_position(self):
        """[新增] 获取窗口当前位置"""
        window = webview.windows[0]
        return {"x": window.x, "y": window.y}

    def window_drag(self, target_x, target_y):
        """[修改] 响应前端的拖拽请求，接收绝对坐标"""
        window = webview.windows[0]
        window.move(target_x, target_y)

    # --- 内部状态管理 ---
    def _clear_session_state(self):
        logger.info("Clearing session state...")
        self.api.update_cookies({})
        self.room_id = ""
        self.csrf = ""
        self.current_area_id = None
        self.current_area_names = []

    # --- 配置管理 ---
    def _load_config(self):
        default_config = {"users": {}, "current_uid": None}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "cookie" in data and "users" not in data:
                        logger.info("Migrating legacy config...")
                        try:
                            temp = util.ck_str_to_dict(data["cookie"])
                            uid = temp.get("DedeUserID", "default")
                            return {
                                "users": {
                                    uid: {
                                        "uid": uid, "uname": "Saved User", "face": "",
                                        "cookie": data.get("cookie", ""), "roomId": data.get("roomId", ""),
                                        "csrf": data.get("csrf", ""), "last_title": data.get("last_title", ""),
                                        "last_area_id": data.get("last_area_id", ""),
                                        "last_area_name": data.get("last_area_name", [])
                                    }
                                },
                                "current_uid": uid
                            }
                        except: pass
                    return data
            except Exception as e:
                logger.error(f"Config load failed: {e}")
        return default_config

    def _save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Save config failed: {e}")

    def _init_current_user(self):
        uid = self.config.get("current_uid")
        users = self.config.get("users", {})
        if uid and uid in users:
            self._clear_session_state()
            user = users[uid]
            logger.info(f"Init user: {user.get('uname')} ({uid})")
            self.api.update_cookies(util.ck_str_to_dict(user.get("cookie", "")))
            self.room_id = user.get("roomId", "")
            self.csrf = user.get("csrf", "")
            self.current_area_id = user.get("last_area_id")
            self.current_area_names = user.get("last_area_name", [])
        else:
            self._clear_session_state()

    def _save_user_data(self, uid, full_data, cookie_str, room_id, csrf):
        uid = str(uid)
        if "users" not in self.config: self.config["users"] = {}
        old_data = self.config["users"].get(uid, {})
        level_info = full_data.get("level_info", {})
        wallet = full_data.get("wallet", {})
        stat = full_data.get("stat", {})
        new_data = {
            "uid": uid, "uname": full_data.get("uname", "未知用户"), "face": full_data.get("face", ""),
            "cookie": cookie_str, "roomId": str(room_id), "csrf": csrf,
            "level": level_info.get("current_level", 0), "current_exp": level_info.get("current_exp", 0),
            "next_exp": level_info.get("next_exp", 0), "money": full_data.get("money", 0),
            "bcoin": wallet.get("bcoin_balance", 0), "following": stat.get("following", 0),
            "follower": stat.get("follower", 0), "dynamic_count": stat.get("dynamic_count", 0),
            "last_title": old_data.get("last_title", ""), "last_area_id": old_data.get("last_area_id", ""),
            "last_area_name": old_data.get("last_area_name", [])
        }
        self.config["users"][uid] = new_data
        self.config["current_uid"] = uid
        self._save_config()
        self.room_id = str(room_id)
        self.csrf = csrf
        self.current_area_id = new_data["last_area_id"]
        self.current_area_names = new_data["last_area_name"]
        return new_data

    # --- 辅助逻辑 ---
    def _fetch_room_id(self, cookies_dict):
        uid = cookies_dict.get("DedeUserID")
        if uid:
            success, res = self.api.get_room_id_by_uid(uid)
            if success:
                if res['code'] == 0: return str(res['data']['room_id'])
                elif res.get('code') == 404: raise Exception("该账号未开通直播间，请先去B站开通。")
        success, res = self.api.get_user_info()
        if success and res['code'] == 0:
            rid = str(res['data'].get('live_room', {}).get('roomid', ''))
            if rid == "0": raise Exception("该账号未开通直播间。")
            return rid
        return ""

    def _fetch_full_user_data(self):
        s1, nav = self.api.get_user_info()
        if not s1 or nav.get('code') != 0: return False, nav
        s2, stat = self.api.get_user_stat()
        stat_data = stat.get('data', {}) if s2 and stat.get('code') == 0 else {}
        full = nav['data']
        full['stat'] = stat_data
        return True, full

    def _get_names_by_id(self, area_id):
        """根据 area_id 反查分区名称 [parent_name, sub_name]"""
        if not self.partition_map:
            self._refresh_partitions_internal()
        
        target_id = str(area_id)
        for p_name, sub_map in self.partition_map.items():
            for s_name, aid in sub_map.items():
                if str(aid) == target_id:
                    return [p_name, s_name]
        return []

    # --- 前端 API 接口 ---
    def load_saved_config(self):
        uid = self.config.get("current_uid")
        users = self.config.get("users", {})
        if uid and uid in users: return {"code": 0, "data": users[uid]}
        return {"code": 0, "data": {}}

    def refresh_current_user(self):
        """刷新当前登录账号的信息"""
        uid = self.config.get("current_uid")
        if not uid or uid not in self.config.get("users", {}):
            return {"code": -1, "msg": "未登录"}

        ok, full_data = self._fetch_full_user_data()
        if ok:
            user = self.config["users"][uid]
            saved_user = self._save_user_data(uid, full_data, user['cookie'], user['roomId'], user['csrf'])
            return {"code": 0, "data": saved_user}
        return {"code": -1, "msg": "刷新失败"}

    def get_account_list(self):
        users = self.config.get("users", {})
        lst = [v for k, v in users.items()]
        return {"code": 0, "data": {"list": lst, "current_uid": self.config.get("current_uid")}}

    def switch_account(self, uid):
        users = self.config.get("users", {})
        if uid in users:
            self.config["current_uid"] = uid
            self._save_config()
            self._init_current_user()
            return {"code": 0, "data": users[uid]}
        return {"code": -1, "msg": "账户不存在"}

    def logout(self, uid):
        users = self.config.get("users", {})
        if uid in users:
            del users[uid]
            if self.config.get("current_uid") == uid:
                self.config["current_uid"] = None
                self._clear_session_state()
            self._save_config()
            return {"code": 0}
        return {"code": -1, "msg": "账户不存在"}

    def get_login_qrcode(self):
        success, res = self.api.get_passport_qrcode()
        return {"code": 0, "data": res['data']} if success and res['code'] == 0 else {"code": -1}

    def poll_login_status(self, key):
        success, res, cookies = self.api.poll_passport_qrcode(key)
        if not success: return {"code": -1, "msg": "网络请求失败"}
        data = res.get('data', {})
        if data.get('code') == 0:
            try:
                self._clear_session_state()
                self.api.update_cookies(cookies)
                csrf = cookies.get('bili_jct', '')
                room_id = self._fetch_room_id(cookies)
                if not room_id: return {"code": -1, "msg": "获取直播间ID失败"}
                ok, full_data = self._fetch_full_user_data()
                if ok:
                    uid = str(cookies.get("DedeUserID"))
                    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                    saved_user = self._save_user_data(uid, full_data, cookie_str, room_id, csrf)
                    self._refresh_partitions_internal()
                    return {"code": 0, "data": saved_user}
                return {"code": -1, "msg": "获取用户信息失败"}
            except Exception as e:
                return {"code": -1, "msg": str(e)}
        return {"code": data.get('code'), "msg": data.get('message')}

    # --- 直播功能 ---
    def _refresh_partitions_internal(self):
        success, res = self.api.get_area_list()
        if success and res.get('code') == 0:
            self.partition_map = {}
            for p in res['data']:
                p_name = p['name']
                self.partition_map[p_name] = {}
                for s in p['list']: self.partition_map[p_name][s['name']] = s['id']
            
            # 刷新后，尝试恢复当前用户的 last_area_id
            uid = self.config.get("current_uid")
            if uid:
                uid = str(uid)
                if uid in self.config["users"]:
                    last_aid = self.config["users"][uid].get("last_area_id")
                    if last_aid: self.current_area_id = last_aid

    def get_partitions(self):
        if not self.partition_map: self._refresh_partitions_internal()
        data = {p: list(s.keys()) for p, s in self.partition_map.items()}
        return {"code": 0, "data": data}

    def update_title(self, title):
        if not self.config.get("current_uid"): return {"code": -1, "msg": "未登录"}
        success, res = self.api.update_title(self.room_id, title, self.csrf)
        if success and res['code'] == 0:
            uid = self.config.get("current_uid")
            if uid:
                uid = str(uid)
                if uid in self.config["users"]:
                    self.config["users"][uid]["last_title"] = title
                    self._save_config()
            return {"code": 0}
        return {"code": -1, "msg": res.get('msg')}

    def update_area(self, p_name, s_name):
        if not self.config.get("current_uid"): return {"code": -1, "msg": "未登录"}
        if not self.partition_map: self._refresh_partitions_internal()
        aid = self.partition_map.get(p_name, {}).get(s_name)
        if not aid: return {"code": -1, "msg": "无效分区"}
        success, res = self.api.update_area(self.room_id, aid, self.csrf)
        if success and res['code'] == 0:
            self.current_area_id = aid
            self.current_area_names = [p_name, s_name]
            uid = self.config.get("current_uid")
            if uid:
                uid = str(uid)
                if uid in self.config["users"]:
                    self.config["users"][uid]["last_area_id"] = aid
                    self.config["users"][uid]["last_area_name"] = [p_name, s_name]
                    self._save_config()
            return {"code": 0}
        return {"code": -1, "msg": res.get('msg')}

    def start_live(self, p_name=None, s_name=None):
        if not self.room_id: return {"code": -1, "msg": "请先登录"}

        # 如果前端传了分区名，先更新内存中的 ID
        if p_name and s_name:
            if not self.partition_map: self._refresh_partitions_internal()
            aid = self.partition_map.get(p_name, {}).get(s_name)
            
            # 如果没找到，尝试强制刷新一次
            if not aid:
                self._refresh_partitions_internal()
                aid = self.partition_map.get(p_name, {}).get(s_name)
            
            if aid:
                self.current_area_id = aid
                self.current_area_names = [p_name, s_name]
            else:
                return {"code": -1, "msg": f"无法识别分区: {p_name}-{s_name}"}

        if not self.current_area_id:
            uid = self.config.get("current_uid")
            if uid:
                uid = str(uid)
                if uid in self.config["users"]:
                    self.current_area_id = self.config["users"][uid].get("last_area_id", "235")
                    # 尝试恢复 names，保持一致性
                    self.current_area_names = self.config["users"][uid].get("last_area_name", [])
                else:
                    self.current_area_id = "235"
            else: self.current_area_id = "235"

        success, res = self.api.start_live(self.room_id, self.current_area_id, self.csrf)
        if success:
            if res['code'] == 0:
                # 成功开启直播后，强制反查一次分区名称，确保数据一致性
                # 这样即使前端没传名字，或者内存中名字丢失，也能补全
                if self.current_area_id:
                    found_names = self._get_names_by_id(self.current_area_id)
                    if found_names:
                        self.current_area_names = found_names

                uid = self.config.get("current_uid")
                if uid:
                    uid = str(uid)
                    if uid in self.config["users"]:
                        self.config["users"][uid]["last_area_id"] = self.current_area_id
                        self.config["users"][uid]["last_area_name"] = self.current_area_names
                        self._save_config()
                return {"code": 0, "data": res['data']['rtmp']}
            elif res['code'] == 60024: return {"code": 60024, "qr": res['data']['qr']}
            return {"code": -1, "msg": res.get('msg')}
        return {"code": -1, "msg": "网络错误"}

    def stop_live(self):
        success, res = self.api.stop_live(self.room_id, self.csrf)
        return {"code": 0} if success and res['code'] == 0 else {"code": -1}

def get_html_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'frontend', 'dist', 'index.html')
    return os.path.join(os.getcwd(), 'frontend', 'dist', 'index.html')

if __name__ == '__main__':
    api = Api()
    window_width = 1000
    window_height = 720
    window = webview.create_window(
        'B站直播工具',
        url=get_html_path(),
        js_api=api,
        width=window_width,
        height=window_height,
        frameless=True,
        easy_drag=False,
        hidden=True
    )
    def center_and_show_window(window):
        primary_screen = webview.screens[0]
        x = (primary_screen.width - window.width) // 2
        y = (primary_screen.height - window.height) // 2
        window.move(x, y)
        window.show()
    webview.start(center_and_show_window, window)