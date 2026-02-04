class SessionState:
    def __init__(self):
        self.room_id = ""
        self.csrf = ""
        self.uid = 0
        self.current_area_id = None
        self.current_area_names = []
        self.is_live = False # 新增直播状态标记

    def clear(self):
        self.room_id = ""
        self.csrf = ""
        self.uid = 0
        self.current_area_id = None
        self.current_area_names = []
        self.is_live = False
