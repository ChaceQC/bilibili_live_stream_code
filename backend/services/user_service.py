import logging
from backend import util

logger = logging.getLogger("UserService")

class UserService:
    def __init__(self, api_client, config_manager, session_state):
        self.api = api_client
        self.config_manager = config_manager
        self.state = session_state

    def init_current_user(self):
        uid = self.config_manager.data.get("current_uid")
        users = self.config_manager.data.get("users", {})
        if uid and uid in users:
            self.state.clear()
            user = users[uid]
            masked_uid = util.mask_string(str(uid))
            logger.info(f"Init user: {user.get('uname')} ({masked_uid})")
            self.api.update_cookies(util.ck_str_to_dict(user.get("cookie", "")))
            self.state.room_id = user.get("roomId", "")
            self.state.csrf = user.get("csrf", "")
            self.state.current_area_id = user.get("last_area_id")
            self.state.current_area_names = user.get("last_area_name", [])
        else:
            logger.info("No current user found, clearing session state.")
            self.state.clear()

    def save_user_data(self, uid, full_data, cookie_str, room_id, csrf):
        uid = str(uid)
        masked_uid = util.mask_string(uid)
        logger.info(f"Saving user data for uid: {masked_uid}")
        
        config_data = self.config_manager.data
        if "users" not in config_data: config_data["users"] = {}
        old_data = config_data["users"].get(uid, {})
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
        config_data["users"][uid] = new_data
        config_data["current_uid"] = uid
        self.config_manager.save()
        
        self.state.room_id = str(room_id)
        self.state.csrf = csrf
        self.state.current_area_id = new_data["last_area_id"]
        self.state.current_area_names = new_data["last_area_name"]
        return new_data

    def fetch_full_user_data(self):
        logger.debug("Fetching full user data...")
        s1, nav = self.api.get_user_info()
        if not s1 or nav.get('code') != 0:
            logger.warning(f"Failed to fetch user info: {nav}")
            return False, nav
        s2, stat = self.api.get_user_stat()
        stat_data = stat.get('data', {}) if s2 and stat.get('code') == 0 else {}
        full = nav['data']
        full['stat'] = stat_data
        return True, full

    def fetch_room_id(self, cookies_dict):
        uid = cookies_dict.get("DedeUserID")
        masked_uid = util.mask_string(str(uid)) if uid else "None"
        logger.debug(f"Fetching room id for uid: {masked_uid}")
        
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

    # --- API Methods ---
    def load_saved_config(self):
        uid = self.config_manager.data.get("current_uid")
        users = self.config_manager.data.get("users", {})
        if uid and uid in users: return {"code": 0, "data": users[uid]}
        return {"code": 0, "data": {}}

    def refresh_current_user(self):
        logger.info("Refreshing current user...")
        uid = self.config_manager.data.get("current_uid")
        if not uid or uid not in self.config_manager.data.get("users", {}):
            logger.warning("Refresh failed: No user logged in.")
            return {"code": -1, "msg": "未登录"}

        ok, full_data = self.fetch_full_user_data()
        if ok:
            user = self.config_manager.data["users"][uid]
            saved_user = self.save_user_data(uid, full_data, user['cookie'], user['roomId'], user['csrf'])
            return {"code": 0, "data": saved_user}
        return {"code": -1, "msg": "刷新失败"}

    def get_account_list(self):
        users = self.config_manager.data.get("users", {})
        lst = [v for k, v in users.items()]
        return {"code": 0, "data": {"list": lst, "current_uid": self.config_manager.data.get("current_uid")}}

    def switch_account(self, uid):
        masked_uid = util.mask_string(str(uid))
        logger.info(f"Switching account to: {masked_uid}")
        users = self.config_manager.data.get("users", {})
        if uid in users:
            self.config_manager.data["current_uid"] = uid
            self.config_manager.save()
            self.init_current_user()
            return {"code": 0, "data": users[uid]}
        logger.warning(f"Switch account failed: User {masked_uid} not found.")
        return {"code": -1, "msg": "账户不存在"}

    def logout(self, uid):
        masked_uid = util.mask_string(str(uid))
        logger.info(f"Logging out user: {masked_uid}")
        users = self.config_manager.data.get("users", {})
        if uid in users:
            del users[uid]
            if self.config_manager.data.get("current_uid") == uid:
                self.config_manager.data["current_uid"] = None
                self.state.clear()
                self.api.update_cookies({})
            self.config_manager.save()
            return {"code": 0}
        logger.warning(f"Logout failed: User {masked_uid} not found.")
        return {"code": -1, "msg": "账户不存在"}
