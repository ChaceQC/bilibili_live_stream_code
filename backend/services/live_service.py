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
                self.state.is_live = True # 标记为正在直播
                
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
                
                # 提取推流码逻辑
                rtmp_data = res['data'].get('rtmp', {})
                protocols = res['data'].get('protocols', [])
                
                # 1. 默认 RTMP-1
                rtmp_addr = rtmp_data.get('addr', '')
                rtmp_code = rtmp_data.get('code', '')
                
                # 2. 提取 RTMP-2 (从 protocols 中找第一个 rtmp 协议且有数据的)
                rtmp2_addr = ""
                rtmp2_code = ""
                for p in protocols:
                    if p.get('protocol') == 'rtmp' and p.get('addr') and p.get('code'):
                        rtmp2_addr = p.get('addr')
                        rtmp2_code = p.get('code')
                        break
                
                # 3. 提取 SRT (从 protocols 中找第一个 srt 协议且有数据的)
                srt_addr = ""
                srt_code = ""
                for p in protocols:
                    if p.get('protocol') == 'srt' and p.get('addr') and p.get('code'):
                        srt_addr = p.get('addr')
                        srt_code = p.get('code')
                        break

                # Mask RTMP address for logging
                logger.info(f"RTMP-1 Addr: {util.mask_string(rtmp_addr, 10, 5)}")
                logger.info(f"RTMP-1 Code: {util.mask_string(rtmp_code, 5, 5)}")
                
                return {
                    "code": 0, 
                    "data": {
                        "rtmp1": {"addr": rtmp_addr, "code": rtmp_code},
                        "rtmp2": {"addr": rtmp2_addr, "code": rtmp2_code},
                        "srt": {"addr": srt_addr, "code": srt_code}
                    }
                }
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
            self.state.is_live = False # 标记为停止直播
            return {"code": 0}
        logger.error(f"Stop live failed: {res}")
        return {"code": -1}
