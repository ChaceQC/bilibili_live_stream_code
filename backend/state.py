class SessionState:
    def __init__(self):
        self.room_id = ""
        self.csrf = ""
        self.current_area_id = None
        self.current_area_names = []

    def clear(self):
        self.room_id = ""
        self.csrf = ""
        self.current_area_id = None
        self.current_area_names = []
