from pydantic import BaseModel, Field, computed_field, ValidationError
import time
from pathlib import Path
from datetime import datetime
import shutil

class Config(BaseModel):
    class MatchSetting(BaseModel):
        max_time: int
        seed_type: list[str]
        bastion_type: list[str]

    class Player(BaseModel):
        name: str
        uuid: str

    player: Player
    clip_setting: dict[str, MatchSetting]
    upload_setting: dict[str, MatchSetting]
    launch_time: float = Field(default_factory=time.time)
    base_dir: Path

    host: str
    port: int

    browser_executable:str

    use_cover: bool

    extra_seconds: int
    replay_prefix: str
    replay_suffix: str
    output_format: str
    filename_formatting: str

    replay_threshold_seconds: int
    clean_raw_file: bool
    use_death_clip: bool
    death_clip_duration: int
    death_clip_ahead_seconds: int

    use_messagebox: bool

    @computed_field
    @property
    def video_dir(self) -> Path:
        path = self.base_dir / "mcsr" / datetime.now().strftime("%Y%m%d")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @computed_field
    @property
    def death_clip_dir(self) -> Path:
        path = self.base_dir / "death_clip" / datetime.now().strftime("%Y%m%d")
        path.mkdir(parents=True, exist_ok=True)

        if not (path / "concat.bat").exists():
            shutil.copy(Path(__file__).parent.parent / "scripts" / "concat.bat", path)
        return path

    @computed_field
    @property
    def template_dir(self) -> Path:
        path = Path(__file__).parent.parent / "templates"
        return path

with open(Path(__file__).parent.parent / "config" / "config.json", "r", encoding="utf8") as f:
    try:
        config = Config.model_validate_json(f.read())
    except ValidationError as exc:
        if exc.errors()[0]['type'] == "json_invalid":
            print(f"'config.json' 文件格式有误：{exc.errors()[0]['msg']}")
        else:
            print(f"解析 'config.json' 文件时出现错误：{'.'.join(exc.errors()[0]['loc'])}"
              f"{exc.errors()[0]['msg']}，实际输入为：{exc.errors()[0]['input']}")
        exit()

if __name__ == "__main__":
    print(config)