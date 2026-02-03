import logging
from backend.bilibili_api import BilibiliApi
from backend.config import Config
from backend.state import SessionState
from backend.services.window_service import WindowService
from backend.services.user_service import UserService
from backend.services.live_service import LiveService
from backend.services.auth_service import AuthService

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
        
        # Initial setup
        self.user_service.init_current_user()

    # --- Window Proxy Methods ---
    def window_min(self): return self.window_service.window_min()
    def window_max(self): return self.window_service.window_max()
    def window_close(self): return self.window_service.window_close(lambda: self.config_manager.save())
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
    def start_live(self, p_name=None, s_name=None): return self.live_service.start_live(p_name, s_name)
    def stop_live(self): return self.live_service.stop_live()
