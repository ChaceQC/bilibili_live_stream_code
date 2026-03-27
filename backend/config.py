import os
import sys
import json
import logging
from backend import util

import shutil  # 用于迁移配置文件

logger = logging.getLogger("Config")

def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # backend/config.py -> backend -> root
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_config_path():
    app_path = get_app_path()
    env_config_home = os.environ.get('BILILIVE_CONFIG_HOME')
    if env_config_home and env_config_home != '':
        return env_config_home

    if sys.platform.startswith('linux'):
        # 给 linux 设置 XDG 标准的 config 位置

        # --- 设置到 config_path ---
        # 这里直接用的构建里面的名字
        APP_NAME = "BiliLiveTool"
        config_home = os.environ.get('XDG_CONFIG_HOME')

        if not config_home or config_home == '':
            # 默认回退到 ~/.config
            config_home = os.path.expanduser('~/.config')
        
        config_path = os.path.join(config_home, APP_NAME)
        
        # 如果不存在则创建目录
        os.makedirs(config_path, exist_ok=True)
        # --- 设置结束 ---

        # --- 迁移之前的配置 ---
        old_config_file = os.path.join(app_path, "config.json")
        new_config_file = os.path.join(config_path, "config.json")

        if not os.path.isfile(new_config_file) and os.path.isfile(old_config_file):
            # 如果新配置文件不存在，且有旧的配置文件
            try:
                shutil.copy(old_config_file, new_config_file)
                logger.info(f"已迁移配置文件: {old_config_file} -> {new_config_file}")
            except Exception as e:
                logger.error(f"配置文件迁移失败: {e}，直接设置配置文件为 {new_config_file}")
        # --- 迁移结束 ---

        return config_path
    else:
        return app_path

CONFIG_FILE = os.path.join(get_config_path(), "config.json")

class Config:
    def __init__(self):
        self.data = self._load_config()

    def _load_config(self):
        default_config = {"users": {}, "current_uid": None, "min_to_tray": True}
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
                                "current_uid": uid,
                                "min_to_tray": True # Default to True
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
