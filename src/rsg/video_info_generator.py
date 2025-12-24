from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rsg.paceman_service import LiveRunData, WorldData, Event
from rsg.description_generator import DescriptionGenerator
from rsg.cover_generator import CoverGenerator
from rsg.rsg_pb import RsgPb
from bilibili_uploader import UploadInfo

import util
from translator import translator
from config import config
from logger import setup_logger

logger = setup_logger(__name__)

class VideoInfoGenerator:
    def __init__(self, live_run: LiveRunData, world_data: WorldData, video_path: Path, rsg_pb: RsgPb):
        self._live_run = live_run
        self._world_data = world_data
        self._video_path = video_path
        self.rsg_pb = rsg_pb

        self._desc_generator = DescriptionGenerator(live_run, world_data, video_path, rsg_pb) if config.use_description else None
        self._cover_generator = CoverGenerator(rsg_pb) if config.use_cover else None

    def _generate_video_title(self):
        def get_event_str(event: Event) -> Optional[str]:
            if not event.is_valid_for_upload():
                return None
            event_str = f"{util.ts_to_str(event.igt)[:5]}{translator.event_map[event.eventId]}"
            if config.use_rsg_pb and self.rsg_pb.is_pb(event):
                event_str += "个人最佳"
            return event_str

        video_title = " ".join(list(filter(None, map(get_event_str, self._live_run.eventList))))
        if (points := self._live_run.get_points()) is not None:
            video_title += f" 积分:{points}"
        title_file_path = config.rsg_video_dir / f'title world[{self._world_data.data.id}].txt'
        with open(title_file_path, 'w', encoding="utf8") as title_file:
            title_file.write(video_title)
        logger.debug(f"视频标题已经输出至{title_file_path}")
        return video_title

    def _generate_video_tags(self):
        v_tag = ["游戏", "单机游戏", "我的世界", "MC", "速通", "MCSR"]
        if self._live_run.eventList[-1].eventId == "rsg.credits":
            v_tag += ["RSG", "完整速通"]
        else:
            v_tag += ["pace", "非完整速通"]
        return v_tag

    def generate(self) -> UploadInfo:
        return UploadInfo(
            id=self._world_data.data.id,
            type="RSG",
            cover_path=self._cover_generator.generate(live_run=self._live_run,
                                                      world_data=self._world_data,
                                                      video_path=self._video_path)
            if self._cover_generator is not None else None,
            video_title=self._generate_video_title(),
            video_desc=self._desc_generator.generate_video_desc()
            if self._desc_generator is not None else "",
            video_tags=self._generate_video_tags(),
            video_path=self._video_path
        )
