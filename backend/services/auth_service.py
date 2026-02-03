class AuthService:
    def __init__(self, api_client, user_service, live_service, session_state):
        self.api = api_client
        self.user_service = user_service
        self.live_service = live_service
        self.state = session_state

    def get_login_qrcode(self):
        success, res = self.api.get_passport_qrcode()
        return {"code": 0, "data": res['data']} if success and res['code'] == 0 else {"code": -1}

    def poll_login_status(self, key):
        success, res, cookies = self.api.poll_passport_qrcode(key)
        if not success: return {"code": -1, "msg": "网络请求失败"}
        data = res.get('data', {})
        if data.get('code') == 0:
            try:
                self.state.clear()
                self.api.update_cookies(cookies)
                csrf = cookies.get('bili_jct', '')
                room_id = self.user_service.fetch_room_id(cookies)
                if not room_id: return {"code": -1, "msg": "获取直播间ID失败"}
                ok, full_data = self.user_service.fetch_full_user_data()
                if ok:
                    uid = str(cookies.get("DedeUserID"))
                    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                    saved_user = self.user_service.save_user_data(uid, full_data, cookie_str, room_id, csrf)
                    self.live_service._refresh_partitions_internal()
                    return {"code": 0, "data": saved_user}
                return {"code": -1, "msg": "获取用户信息失败"}
            except Exception as e:
                return {"code": -1, "msg": str(e)}
        return {"code": data.get('code'), "msg": data.get('message')}
