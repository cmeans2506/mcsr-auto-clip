from pydantic import BaseModel, Field, computed_field
import time
from pathlib import Path
from datetime import datetime

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

    @computed_field
    @property
    def video_dir(self) -> Path:
        path = self.base_dir / "mcsr" / datetime.now().strftime("%Y%m%d")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @computed_field
    @property
    def template_dir(self) -> Path:
        path = Path(__file__).parent.parent / "templates"
        return path

with open(f"../config/config.json", "r", encoding="utf8") as f:
    config = Config.model_validate_json(f.read())

if __name__ == "__main__":
    print(config)