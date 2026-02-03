import logging
import asyncio
import threading
from backend.bilibili_api import BilibiliApi
from backend.config import Config
from backend.state import SessionState
from backend.services.window_service import WindowService
from backend.services.user_service import UserService
from backend.services.live_service import LiveService
from backend.services.auth_service import AuthService
from backend.services.danmu_service import DanmuService

logger = logging.getLogger("ApiService")

class ApiService:
    def __init__(self):
        self.api_client = BilibiliApi()
        self.config_manager = Config()
        self.session_state = SessionState()
        
        # Initialize services
        self.window_service = WindowService()
        self.user_service = UserService(self.api_client, self.config_manager, self.session_state)
        self.live_service = LiveService(self.api_client, self.config_manager, self.session_state)
        self.auth_service = AuthService(self.api_client, self.user_service, self.live_service, self.session_state)
        self.danmu_service = DanmuService(self.api_client, self.session_state)
        
        # 设置弹幕回调
        self.danmu_service.set_callback(self._on_danmu_message)
        self.danmu_service.set_log_callback(self._on_backend_log)
        
        # Initial setup
        self.user_service.init_current_user()
        
        # Asyncio loop for danmu
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._start_loop, args=(self.loop,), daemon=True)
        self.loop_thread.start()

    def _start_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def _on_danmu_message(self, data):
        """处理弹幕消息回调，推送到前端"""
        # 注意：这里可能在子线程中被调用，webview 的 evaluate_js 应该是线程安全的
        # 前端挂载的函数名为 onDanmuMessage
        self.window_service.send_to_frontend("onDanmuMessage", data)

    def _on_backend_log(self, msg):
        """处理后端日志回调，推送到前端"""
        self.window_service.send_to_frontend("onBackendLog", msg)

    # --- Window Proxy Methods ---
    def window_min(self): return self.window_service.window_min()
    def window_max(self): return self.window_service.window_max()
    def window_close(self): 
        asyncio.run_coroutine_threadsafe(self.danmu_service.stop(), self.loop)
        return self.window_service.window_close(lambda: self.config_manager.save())
    def get_window_position(self): return self.window_service.get_window_position()
    def window_drag(self, target_x, target_y): return self.window_service.window_drag(target_x, target_y)

    # --- User Proxy Methods ---
    def load_saved_config(self): return self.user_service.load_saved_config()
    def refresh_current_user(self): return self.user_service.refresh_current_user()
    def get_account_list(self): return self.user_service.get_account_list()
    def switch_account(self, uid): return self.user_service.switch_account(uid)
    def logout(self, uid): return self.user_service.logout(uid)

    # --- Auth Proxy Methods ---
    def get_login_qrcode(self): return self.auth_service.get_login_qrcode()
    def poll_login_status(self, key): return self.auth_service.poll_login_status(key)

    # --- Live Proxy Methods ---
    def get_partitions(self): return self.live_service.get_partitions()
    def update_title(self, title): return self.live_service.update_title(title)
    def update_area(self, p_name, s_name): return self.live_service.update_area(p_name, s_name)
    def start_live(self, p_name=None, s_name=None): 
        res = self.live_service.start_live(p_name, s_name)
        if res['code'] == 0:
             # 开启直播成功后，连接弹幕
             room_id = self.session_state.room_id
             if room_id:
                 asyncio.run_coroutine_threadsafe(self.danmu_service.connect(room_id), self.loop)
        return res
        
    def stop_live(self): 
        res = self.live_service.stop_live()
        if res['code'] == 0:
            asyncio.run_coroutine_threadsafe(self.danmu_service.stop(), self.loop)
        return res

    # --- Danmu Methods ---
    def start_danmu_monitor(self):
        """手动开启弹幕监听（用于测试或非开播状态）"""
        room_id = self.session_state.room_id
        if not room_id:
             return {"code": -1, "msg": "未获取到房间ID"}
        asyncio.run_coroutine_threadsafe(self.danmu_service.connect(room_id), self.loop)
        return {"code": 0}

    def stop_danmu_monitor(self):
        asyncio.run_coroutine_threadsafe(self.danmu_service.stop(), self.loop)
        return {"code": 0}
