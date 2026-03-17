from pathlib import Path
from typing import Optional

from base.base_video_info_generator import BaseVideoInfoGenerator
from rsg.paceman_service import LiveRunData, Event
from rsg.description_generator import DescriptionGenerator
from rsg.cover_generator import CoverGenerator
from rsg.rsg_pb import RsgPb
from bilibili_uploader import UploadInfo, VideoType

import util
from config import config
from logger import setup_logger

logger = setup_logger(__name__)


class VideoInfoGenerator(BaseVideoInfoGenerator):
    def __init__(self, live_run: LiveRunData, video_path: Path, rsg_pb: RsgPb):
        super().__init__()
        self.live_run = live_run
        self.rsg_pb = rsg_pb
        self.video_path = video_path


    def get_video_title(self) -> str:
        def get_event_str(event: Event) -> Optional[str]:
            if not event.is_valid_for_upload():
                return None
            event_str = f"{util.ts_to_str_sec(event.igt)}{event.eventId.label}"
            if config.use_rsg_pb and self.rsg_pb.is_pb(event):
                event_str += "PB"
            return event_str

        return " ".join(list(filter(None, map(get_event_str, self.live_run.eventList))))


    def get_title_file_path(self) -> Path:
        return config.ranked_video_dir / f'title[{self.live_run.id}].txt'


    def get_video_id(self) -> int:
        return self.live_run.id


    def get_video_type(self) -> VideoType:
        return "RSG"


    def generate_video_cover(self) -> Optional[Path]:
        if not config.use_cover:
            return None
        return CoverGenerator(live_run=self.live_run, video_path=self.video_path, rsg_pb=self.rsg_pb).generate()


    def generate_video_desc(self) -> str:
        if not config.use_description:
            return ""
        return DescriptionGenerator(live_run=self.live_run, video_path=self.video_path, rsg_pb=self.rsg_pb).generate()

    def generate_video_tags(self) -> list[str]:
        v_tag = ["Minecraft", "MC", "Speedrun", "MCSR"]
        if self.live_run.is_complete_run:
            v_tag += ["RSG", "Complete Run"]
        else:
            v_tag += ["pace", "Incomplete Run"]
        return v_tag

    def get_video_path(self) -> Path:
        return self.video_path

