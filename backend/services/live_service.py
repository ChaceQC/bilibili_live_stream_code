import logging
from backend import util

logger = logging.getLogger("LiveService")

class LiveService:
    def __init__(self, api_client, config_manager, session_state):
        self.api = api_client
        self.config_manager = config_manager
        self.state = session_state
        self.partition_map = {}

    def _refresh_partitions_internal(self):
        logger.debug("Refreshing partitions...")
        success, res = self.api.get_area_list()
        if success and res.get('code') == 0:
            self.partition_map = {}
            for p in res['data']:
                p_name = p['name']
                self.partition_map[p_name] = {}
                for s in p['list']: self.partition_map[p_name][s['name']] = s['id']
            
            # 刷新后，尝试恢复当前用户的 last_area_id
            uid = self.config_manager.data.get("current_uid")
            if uid:
                uid = str(uid)
                if uid in self.config_manager.data["users"]:
                    last_aid = self.config_manager.data["users"][uid].get("last_area_id")
                    if last_aid: self.state.current_area_id = last_aid
        else:
            logger.error(f"Failed to refresh partitions: {res}")

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

    # --- API Methods ---
    def get_partitions(self):
        if not self.partition_map: self._refresh_partitions_internal()
        data = {p: list(s.keys()) for p, s in self.partition_map.items()}
        return {"code": 0, "data": data}

    def update_title(self, title):
        logger.info(f"Updating title to: {title}")
        if not self.config_manager.data.get("current_uid"): return {"code": -1, "msg": "未登录"}
        success, res = self.api.update_title(self.state.room_id, title, self.state.csrf)
        if success and res['code'] == 0:
            uid = self.config_manager.data.get("current_uid")
            if uid:
                uid = str(uid)
                if uid in self.config_manager.data["users"]:
                    self.config_manager.data["users"][uid]["last_title"] = title
                    self.config_manager.save()
            return {"code": 0}
        logger.error(f"Update title failed: {res}")
        return {"code": -1, "msg": res.get('msg')}

    def update_area(self, p_name, s_name):
        logger.info(f"Updating area to: {p_name} - {s_name}")
        if not self.config_manager.data.get("current_uid"): return {"code": -1, "msg": "未登录"}
        if not self.partition_map: self._refresh_partitions_internal()
        aid = self.partition_map.get(p_name, {}).get(s_name)
        if not aid:
            logger.warning(f"Invalid area: {p_name} - {s_name}")
            return {"code": -1, "msg": "无效分区"}
        success, res = self.api.update_area(self.state.room_id, aid, self.state.csrf)
        if success and res['code'] == 0:
            self.state.current_area_id = aid
            self.state.current_area_names = [p_name, s_name]
            uid = self.config_manager.data.get("current_uid")
            if uid:
                uid = str(uid)
                if uid in self.config_manager.data["users"]:
                    self.config_manager.data["users"][uid]["last_area_id"] = aid
                    self.config_manager.data["users"][uid]["last_area_name"] = [p_name, s_name]
                    self.config_manager.save()
            return {"code": 0}
        logger.error(f"Update area failed: {res}")
        return {"code": -1, "msg": res.get('msg')}

    def start_live(self, p_name=None, s_name=None):
        logger.info("Starting live stream...")
        if not self.state.room_id: return {"code": -1, "msg": "请先登录"}

        # 如果前端传了分区名，先更新内存中的 ID
        if p_name and s_name:
            if not self.partition_map: self._refresh_partitions_internal()
            aid = self.partition_map.get(p_name, {}).get(s_name)
            
            # 如果没找到，尝试强制刷新一次
            if not aid:
                self._refresh_partitions_internal()
                aid = self.partition_map.get(p_name, {}).get(s_name)
            
            if aid:
                self.state.current_area_id = aid
                self.state.current_area_names = [p_name, s_name]
            else:
                logger.warning(f"Unknown partition: {p_name}-{s_name}")
                return {"code": -1, "msg": f"无法识别分区: {p_name}-{s_name}"}

        if not self.state.current_area_id:
            uid = self.config_manager.data.get("current_uid")
            if uid:
                uid = str(uid)
                if uid in self.config_manager.data["users"]:
                    self.state.current_area_id = self.config_manager.data["users"][uid].get("last_area_id", "235")
                    # 尝试恢复 names，保持一致性
                    self.state.current_area_names = self.config_manager.data["users"][uid].get("last_area_name", [])
                else:
                    self.state.current_area_id = "235"
            else: self.state.current_area_id = "235"

        success, res = self.api.start_live(self.state.room_id, self.state.current_area_id, self.state.csrf)
        if success:
            if res['code'] == 0:
                logger.info("Live stream started successfully.")
                # 成功开启直播后，强制反查一次分区名称，确保数据一致性
                if self.state.current_area_id:
                    found_names = self._get_names_by_id(self.state.current_area_id)
                    if found_names:
                        self.state.current_area_names = found_names

                uid = self.config_manager.data.get("current_uid")
                if uid:
                    uid = str(uid)
                    if uid in self.config_manager.data["users"]:
                        self.config_manager.data["users"][uid]["last_area_id"] = self.state.current_area_id
                        self.config_manager.data["users"][uid]["last_area_name"] = self.state.current_area_names
                        self.config_manager.save()
                
                # Mask RTMP address for logging
                rtmp_addr = res['data']['rtmp'].get('addr', '')
                rtmp_code = res['data']['rtmp'].get('code', '')
                logger.info(f"RTMP Addr: {util.mask_string(rtmp_addr, 10, 5)}")
                logger.info(f"RTMP Code: {util.mask_string(rtmp_code, 5, 5)}")
                
                return {"code": 0, "data": res['data']['rtmp']}
            elif res['code'] == 60024:
                logger.info("Live stream requires face verification (60024).")
                return {"code": 60024, "qr": res['data']['qr']}
            
            logger.error(f"Start live failed: {res}")
            return {"code": -1, "msg": res.get('msg')}
        
        logger.error("Start live failed: Network error")
        return {"code": -1, "msg": "网络错误"}

    def stop_live(self):
        logger.info("Stopping live stream...")
        success, res = self.api.stop_live(self.state.room_id, self.state.csrf)
        if success and res['code'] == 0:
            logger.info("Live stream stopped successfully.")
            return {"code": 0}
        logger.error(f"Stop live failed: {res}")
        return {"code": -1}
