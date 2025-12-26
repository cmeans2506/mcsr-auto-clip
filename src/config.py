from pydantic import BaseModel, Field, ValidationError
import time
from pathlib import Path
from datetime import datetime
import shutil
import sys
import os

VERSION = "v1.0.1"
app_name = "mcsr auto clip"
config_dir = Path(os.environ["APPDATA"]) / app_name
config_dir.mkdir(parents=True, exist_ok=True)
# ==========================================
# 默认配置
# ==========================================

DEFAULT_PLAYER = {
    "name": "Cmeans",
    "uuid": "3affdb407396456abcca42dbeb102331"
}

DEFAULT_MATCH = {
    "max_time": 720000,
    "seed_type": ["BURIED_TREASURE", "SHIPWRECK", "VILLAGE", "DESERT_TEMPLE", "RUINED_PORTAL"],
    "bastion_type": ["BRIDGE", "STABLES", "HOUSING", "TREASURE"]
}

EMPTY_MATCH = {"max_time": 0, "seed_type": [], "bastion_type": []}

DEFAULT_CLIP_SETTING = {
    "ranked": {
        "CASUAL_MATCH": EMPTY_MATCH,
        "RANKED_MATCH": {**DEFAULT_MATCH, "max_time": 720000},
        "PRIVATE_ROOM_MATCH": {**DEFAULT_MATCH, "max_time": 660000},
        "EVNET_MODE_MATCH": EMPTY_MATCH
    },
    "rsg": {
        "rsg.enter_nether": 0, "rsg.enter_bastion": 0, "rsg.enter_fortress": 0,
        "rsg.first_portal": 540000, "rsg.enter_stronghold": 660000,
        "rsg.enter_end": 720000, "rsg.credits": 900000
    }
}

DEFAULT_UPLOAD_SETTING = {
    "ranked": {
        "CASUAL_MATCH": EMPTY_MATCH,
        "RANKED_MATCH": {**DEFAULT_MATCH, "max_time": 660000},
        "PRIVATE_ROOM_MATCH": {**DEFAULT_MATCH, "max_time": 600000},
        "EVNET_MODE_MATCH": EMPTY_MATCH
    },
    "rsg": {
        "rsg.enter_nether": 0, "rsg.enter_bastion": 0, "rsg.enter_fortress": 0,
        "rsg.first_portal": 480000, "rsg.enter_stronghold": 600000,
        "rsg.enter_end": 660000, "rsg.credits": 840000
    }
}


def get_working_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent.parent


class MatchSetting(BaseModel):
    max_time: int
    seed_type: list[str]
    bastion_type: list[str]


class Setting(BaseModel):
    ranked: dict[str, MatchSetting]
    rsg: dict[str, int]


class Player(BaseModel):
    name: str
    uuid: str


class Config(BaseModel):
    player: Player = Field(default_factory=lambda: Player(**DEFAULT_PLAYER))
    clip_setting: Setting = Field(default_factory=lambda: Setting(**DEFAULT_CLIP_SETTING))
    upload_setting: Setting = Field(default_factory=lambda: Setting(**DEFAULT_UPLOAD_SETTING))
    launch_time: float = Field(default_factory=time.time, exclude=True)
    base_dir: Path = Field(default=Path.home() / "Desktop" / "mcsr videos")
    working_dir: Path = Field(default_factory=get_working_dir, exclude=True)

    host: str = Field(default="localhost")
    port: int = Field(default=4455)

    browser_executable: Path = Field(default=Path.home() / "chromium" / "chrome-win" / "chrome.exe")
    use_cover: bool = Field(default=False)
    use_description: bool = Field(default=False)
    use_upload: bool = Field(default=False)
    use_rsg_pb: bool = Field(default=False)

    extra_seconds: int = Field(default=15)
    wait_for_datapack: int = Field(default=20)

    replay_threshold_seconds: int = Field(default=20)
    clean_raw_file: bool = Field(default=True)
    use_death_clip: bool = Field(default=True)
    ranked_job: bool = Field(default=True)
    rsg_job: bool = Field(default=True)
    death_clip_duration: int = Field(default=20)
    death_clip_ahead_seconds: int = Field(default=0)


    @property
    def rsg_video_dir(self) -> Path:
        path = self.base_dir / "rsg" / datetime.now().strftime("%Y%m%d")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def ranked_video_dir(self) -> Path:
        path = self.base_dir / "ranked" / datetime.now().strftime("%Y%m%d")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def death_clip_dir(self) -> Path:
        path = self.base_dir / "death_clip" / datetime.now().strftime("%Y%m%d")
        path.mkdir(parents=True, exist_ok=True)

        if not (path / "concat.bat").exists():
            shutil.copy(self.working_dir / "scripts" / "concat.bat", path)
        return path

    @property
    def template_dir(self) -> Path:
        path = self.working_dir / "templates"
        return path

    @property
    def log_dir(self) -> Path:
        path = self.base_dir / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save(self):
        json_data = self.model_dump_json(indent=2)

        with open(config_dir / "config.json", "w", encoding="utf8") as config_f:
            config_f.write(json_data)

    @classmethod
    def from_config_dir(cls, conf_dir: Path):
        config_file_path = conf_dir / "config.json"
        if not config_file_path.exists():
            instance = Config()
            return instance

        with open(config_file_path, "r", encoding="utf8") as f:
            file_content = f.read()
        try:
            instance = Config.model_validate_json(file_content)
        except ValidationError as exc:
            if exc.errors()[0]['type'] == "json_invalid":
                print(f"'config.json' 文件格式有误：{exc.errors()[0]['msg']}")
            else:
                print(f"解析 'config.json' 文件时出现错误：{'.'.join(exc.errors()[0]['loc'])}，"
                      f"{exc.errors()[0]['msg']}，实际输入为：{exc.errors()[0]['input']}")
            print("使用默认的config配置")
            instance = Config()
        return instance

config = Config.from_config_dir(config_dir)


if __name__ == "__main__":
    print(Config.model_fields["player"].default_factory())
    print(Config.model_fields["host"].default)
    print(config)