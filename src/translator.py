import json
from pathlib import Path
from config import config


class Translator:
    def __init__(self):
        with open(config.working_dir / "config" / "translator.json", "r", encoding="utf8") as tr_file:
            tr_info = json.load(tr_file)
            self.event_map: dict[str, str] = tr_info["event_map"]
            self.timeline_map: dict[str, str] = tr_info["timeline_map"]
            self.seedtype_map: dict[str, str] = tr_info["seedtype_map"]
            self.bastion_map: dict[str, str] = tr_info["bastion_map"]
            self.match_type_map: dict[str, str] = tr_info["match_type_map"]

            self.event_map_rev = {v: k for k, v in self.event_map.items()}
            self.timeline_map_rev = {v: k for k, v in self.timeline_map.items()}
            self.seedtype_map_rev = {v: k for k, v in self.seedtype_map.items()}
            self.bastion_map_rev = {v: k for k, v in self.bastion_map.items()}
            self.match_type_map_rev = {v: k for k, v in self.match_type_map.items()}

translator = Translator()

