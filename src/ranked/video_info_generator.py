from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ranked.ranked_service import MatchData, UserData, MatchInfo, MatchType
from ranked.description_generator import DescriptionGenerator
from ranked.cover_generator import CoverGenerator
from bilibili_uploader import UploadInfo

import util
from translator import translator
from config import config
from logger import setup_logger

logger = setup_logger(__name__)

class VideoInfoGenerator:
    def __init__(self, match_data: MatchData, match_info: MatchInfo, user_data: UserData, video_path: Path):
        self._match_data = match_data
        self._match_info = match_info
        self._user_data = user_data
        self._video_path = video_path


        self._desc_generator = DescriptionGenerator(match_data=match_data,
                                                    user_data=user_data,
                                                    video_path=video_path) if config.use_description else None
        self._cover_generator = CoverGenerator() if config.use_description else None

    def _generate_video_title(self) -> str:
        title = f"RANKED {util.ts_to_str(self._match_data.result.time)}"
        if (self._match_data.type_ == MatchType.RANKED_MATCH
                and self._match_data.result.time <= self._user_data.statistics.total.bestTime.ranked):
            title += " 个人最佳"
        if self._match_data.type_ == MatchType.PRIVATE_ROOM_MATCH:
            title += " 私人房间"
        title += (f" {translator.seedtype_map[self._match_data.seedType]} "
                  f"{translator.bastion_map[self._match_data.bastionType]}")
        title_file_path = config.ranked_video_dir / f'title match[{self._match_data.id_}].txt'
        with open(title_file_path, 'w', encoding="utf8") as title_file:
            title_file.write(title)
        logger.debug(f"视频标题已经输出至{title_file_path}")
        return title

    def generate(self) -> UploadInfo:
        return UploadInfo(id=self._match_info.id_,
                          type="RANKED",
                          cover_path=self._cover_generator.generate(video_path=self._video_path,
                                                                    match_info=self._match_info)
                          if self._desc_generator is not None else None,
                          video_title=self._generate_video_title(),
                          video_desc=self._desc_generator.generate_video_desc()
                          if self._desc_generator is not None else "",
                          video_tags=["游戏", "单机游戏", "我的世界", "MC", "速通", "MCSR", "RANKED", "速通排位赛"],
                          video_path=self._video_path,
                          )
