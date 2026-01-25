from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ranked.ranked_service import MatchData, UserData, MatchInfo, MatchType
from ranked.description_generator import DescriptionGenerator
from ranked.cover_generator import CoverGenerator
from bilibili_uploader import VideoType

import util
from config import config
from base.base_video_info_generator import BaseVideoInfoGenerator
from logger import setup_logger

logger = setup_logger(__name__)

class VideoInfoGenerator(BaseVideoInfoGenerator):
    def __init__(self, match_data: MatchData, match_info: MatchInfo, user_data: UserData, video_path: Path):
        super().__init__()
        self.match_data = match_data
        self.match_info = match_info
        self.user_data = user_data
        self.video_path = video_path

    def get_video_title(self) -> str:
        title = f"RANKED {util.ts_to_str_sec(self.match_data.result.time)}"
        if (self.match_data.type_ == MatchType.RANKED_MATCH
                and self.match_data.result.time <= self.user_data.statistics.total.bestTime.ranked):
            title += " 个人最佳"
        if self.match_data.type_ == MatchType.PRIVATE_ROOM_MATCH:
            title += " 私人房间"
        return title

    def get_title_file_path(self) -> Path:
        return config.ranked_video_dir / f'title[{self.match_data.id_}].txt'


    def get_video_id(self) -> int:
        return self.match_data.id_


    def get_video_type(self) -> VideoType:
        return "RANKED"


    def generate_video_cover(self) -> Optional[Path]:
        if not config.use_cover:
            return None
        return CoverGenerator(video_path=self.video_path, match_info=self.match_info).generate()


    def generate_video_desc(self) -> str:
        if not config.use_description:
            return ""
        return DescriptionGenerator(
            match_data=self.match_data,
            user_data=self.user_data,
            video_path=self.video_path
        ).generate()

    def generate_video_tags(self) -> list[str]:
        return ["游戏", "单机游戏", "我的世界", "MC", "速通", "MCSR", "RANKED", "速通排位赛"]

    def get_video_path(self) -> Path:
        return self.video_path

