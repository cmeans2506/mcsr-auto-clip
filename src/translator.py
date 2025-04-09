import json


class Translator:
    def __init__(self):
        with open("../config/translator.json", "r", encoding="utf8") as tr_file:
            tr_info = json.load(tr_file)
            self.event_map = tr_info["event_map"]
            self.timeline_map = tr_info["timeline_map"]
            self.seedtype_map = tr_info["seedtype_map"]
            self.bastion_map = tr_info["bastion_map"]
            self.match_type_map = tr_info["match_type_map"]

translator = Translator()

