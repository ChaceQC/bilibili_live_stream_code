class SessionState:
    def __init__(self):
        self.room_id = ""
        self.csrf = ""
        self.uid = 0
        self.current_area_id = None
        self.current_area_names = []

    def clear(self):
        self.room_id = ""
        self.csrf = ""
        self.uid = 0
        self.current_area_id = None
        self.current_area_names = []
