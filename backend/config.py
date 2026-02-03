import os
import sys
import json
import logging
from backend import util

logger = logging.getLogger("Config")

def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # backend/config.py -> backend -> root
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(get_app_path(), "config.json")

class Config:
    def __init__(self):
        self.data = self._load_config()

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

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Save config failed: {e}")
