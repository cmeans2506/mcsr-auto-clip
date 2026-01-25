from pathlib import Path
from typing import Optional

from base.base_video_info_generator import BaseVideoInfoGenerator
from rsg.paceman_service import LiveRunData, WorldData, Event
from rsg.description_generator import DescriptionGenerator
from rsg.cover_generator import CoverGenerator
from rsg.rsg_pb import RsgPb
from bilibili_uploader import UploadInfo, VideoType

import util
from translator import translator
from config import config
from logger import setup_logger

logger = setup_logger(__name__)


class VideoInfoGenerator(BaseVideoInfoGenerator):
    def __init__(self, live_run: LiveRunData, world_data: WorldData, video_path: Path, rsg_pb: RsgPb):
        super().__init__()
        self.live_run = live_run
        self.world_data = world_data
        self.rsg_pb = rsg_pb
        self.video_path = video_path


    def get_video_title(self) -> str:
        def get_event_str(event: Event) -> Optional[str]:
            if not event.is_valid_for_upload():
                return None
            event_str = f"{util.ts_to_str_sec(event.igt)}{translator.event_map[event.eventId]}"
            if config.use_rsg_pb and self.rsg_pb.is_pb(event):
                event_str += "个人最佳"
            return event_str

        video_title = " ".join(list(filter(None, map(get_event_str, self.live_run.eventList))))
        if (points := self.live_run.get_points()) is not None:
            video_title += f" 积分:{points}"
        return video_title


    def get_title_file_path(self) -> Path:
        return config.ranked_video_dir / f'title[{self.world_data.data.id}].txt'


    def get_video_id(self) -> int:
        return self.world_data.data.id


    def get_video_type(self) -> VideoType:
        return "RSG"


    def generate_video_cover(self) -> Optional[Path]:
        if not config.use_cover:
            return None
        return CoverGenerator(
            live_run=self.live_run, world_data=self.world_data,
            video_path=self.video_path, rsg_pb=self.rsg_pb
        ).generate()


    def generate_video_desc(self) -> str:
        if not config.use_description:
            return ""
        return DescriptionGenerator(
            live_run=self.live_run, world_data=self.world_data,
            video_path=self.video_path, rsg_pb=self.rsg_pb
        ).generate()

    def generate_video_tags(self) -> list[str]:
        v_tag = ["游戏", "单机游戏", "我的世界", "MC", "速通", "MCSR"]
        if self.live_run.eventList[-1].eventId == "rsg.credits":
            v_tag += ["RSG", "完整速通"]
        else:
            v_tag += ["pace", "非完整速通"]
        return v_tag

    def get_video_path(self) -> Path:
        return self.video_path

