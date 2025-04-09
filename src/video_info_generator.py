from dataclasses import dataclass
from pathlib import Path
from ranked_service import MatchData, UserData, MatchInfo
from description_generator import DescriptionGenerator
from cover_generator import CoverGenerator
import util
from translator import translator
from typing import Optional
from config import config

class VideoInfoGenerator:
    @dataclass
    class VideoInfo:
        cover_path: Optional[Path]
        video_title: str
        video_desc: str
        video_tags: list[str]
        video_path: Path
        match_data: MatchData

    def __init__(self, match_data: MatchData, match_info: MatchInfo, user_data: UserData, video_path: Path):
        self._match_data = match_data
        self._match_info = match_info
        self._user_data = user_data
        self._video_path = video_path

        self._desc_generator = DescriptionGenerator(match_data=match_data, user_data=user_data, video_path=video_path)
        if config.use_cover:
            self._cover_generator = CoverGenerator()

    def _generate_video_title(self) -> str:
        title = f"RANKED {util.ts_to_str(self._match_data.result.time)}"
        if self._match_data.result.time <= self._user_data.statistics.total.bestTime.ranked:
            title += " 个人最佳"
        title += f" {translator.seedtype_map[self._match_data.seedType]} {translator.bastion_map[self._match_data.bastionType]}"
        return title

    def generate(self) -> VideoInfo:
        return VideoInfoGenerator.VideoInfo(
            cover_path=self._cover_generator.generate(video_path=self._video_path, match_info=self._match_info)
            if config.use_cover else None,
            video_title=self._generate_video_title(),
            video_desc=self._desc_generator.generate_video_desc(),
            video_tags=["游戏", "单机游戏", "我的世界", "MC", "速通", "MCSR", "RANKED", "速通排位赛"],
            video_path=self._video_path,
            match_data=self._match_data
        )
