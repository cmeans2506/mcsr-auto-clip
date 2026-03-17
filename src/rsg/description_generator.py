import inspect
from pathlib import Path
from datetime import datetime
import time
from string import Template
from PyQt6.QtCore import QCoreApplication

from base.base_description_generator import BaseDescriptionGenerator
from config import config
import util
from rsg.paceman_service import LiveRunData, Event, User, EventIdType
from rsg.rsg_pb import RsgPb
from logger import setup_logger

logger = setup_logger(__name__)


class DescriptionGenerator(BaseDescriptionGenerator):
    def __init__(self, live_run: LiveRunData, video_path: Path, rsg_pb: RsgPb):
        self._live_run = live_run
        self._video_path = video_path
        self.rsg_pb = rsg_pb
        super().__init__(video_path=video_path)
        self.sub_template = Template(inspect.cleandoc(
            QCoreApplication.translate("RSGDescriptionGenerator", """                    
            ■ Timelines
            $timelines_info

            ■ PB Info
            $pb_info

        """)))


    def _generate_timelines_info(self):
        def event_to_str(event: Event) -> str:
            event_str = f"{util.ts_to_str_sec(event.igt)} {event.eventId.label}"
            if config.use_rsg_pb and self.rsg_pb.is_pb(event):
                event_str += " pb"
            return event_str

        event_list = self._live_run.eventList
        return " || ".join(list(map(event_to_str, event_list)))

    def _generate_pb_info(self):
        if not config.use_rsg_pb:
            return None
        def get_pb_str(key: EventIdType):
            if not self.rsg_pb.pb_info[key].igt:
                return ""
            pb_time = datetime.fromtimestamp(self.rsg_pb.pb_info[key].time).strftime("%Y-%m-%d")
            pb_str = (f"·{key.label}\t{util.ts_to_str(self.rsg_pb.pb_info[key].igt)}"
                      f" | {pb_time}"
                      f" | {int((time.time() - self.rsg_pb.pb_info[key].time) / (60 * 60 * 24))} days ago"
                      f" | link: {self.rsg_pb.pb_info[key].bvid}")
            return pb_str

        return "\n".join(list(filter(None, map(get_pb_str, self.rsg_pb.pb_info))))


    def generate_upload_reason(self):
        CIRCLE_NUMBERS = "①②③④⑤⑥⑦⑧⑨⑩"
        i = 0
        upload_reason = ""
        upload_setting_list = []
        for key in config.upload_setting.rsg:
            # 时间设为 0 表示忽略
            if config.upload_setting.rsg[key] == 0:
                continue
            upload_setting_list.append(f"{CIRCLE_NUMBERS[i]} sub"
                              f"{util.ts_to_str_sec(config.upload_setting.rsg[key])} "
                              f"{EventIdType(key).label}")
            i += 1
        upload_reason += " | ".join(upload_setting_list)
        upload_reason += "\nThis run satisfies: \n"

        upload_reason_list = []
        i = 0
        for event in self._live_run.eventList:
            if event.igt < config.upload_setting.rsg[event.eventId]:
                upload_reason_list.append(f"{CIRCLE_NUMBERS[i]} sub"
                                          f"{util.ts_to_str_sec(config.upload_setting.rsg[event.eventId])} "
                                          f"{event.eventId.label}")
                i += 1
        upload_reason += " | ".join(upload_reason_list) or "None"
        return upload_reason


    def generate_about_info(self):
        return inspect.cleandoc(f"""

            · paceman：https://paceman.gg/stats/run/{self._live_run.id}/
            · api：https://paceman.gg/stats/api/getWorld/?worldId={self._live_run.id}

        """)

    def generate_sub_template(self) -> str:
        return self.sub_template.safe_substitute(
            timelines_info=self._generate_timelines_info(),
            pb_info=self._generate_pb_info() or "None",
        )

    def get_desc_path(self) -> Path:
        return config.rsg_video_dir / f'desc[{self._live_run.id}].txt'


if __name__ == '__main__':

    _desc_generator = DescriptionGenerator(
        live_run=LiveRunData(
            id=123456,
            worldId="3824376fdaf982a2e999f6fb8c075dd4149ef441e586689dcbb55b781d69cc0c",
            gameVersion="1.16.1",
            eventList=[
                Event(
                    eventId="rsg.enter_nether",
                    rta=197409,
                    igt=195323
                ),
                Event(
                    eventId="rsg.enter_bastion",
                    rta=292811,
                    igt=285575
                ),
                Event(
                    eventId="rsg.enter_fortress",
                    rta=594661,
                    igt=582525
                ),
                Event(
                    eventId="rsg.first_portal",
                    rta=777972,
                    igt=765566
                ),
                Event(
                    eventId="rsg.second_portal",
                    rta=992321,
                    igt=957276
                ),
                Event(
                    eventId="rsg.enter_stronghold",
                    rta=992376,
                    igt=957276
                )
            ],
            user=User(
                uuid="8ee48ee6-7cfe-495a-8051-40d7a31ebb91",
            ),
            isCheated=False,
            isHidden=False,
            lastUpdated=1753606925065,
            nickname="Wojcio234"
        ),
        video_path=Path(r"D:\OBS VIdeos\2025-03-06 15-52-44.mp4"),
        rsg_pb=RsgPb()
    )

    print(_desc_generator.generate())
