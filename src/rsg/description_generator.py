import inspect
from pathlib import Path
from datetime import datetime
import time
from string import Template

from base.base_description_generator import BaseDescriptionGenerator
from config import config
from translator import translator
import util
from rsg.paceman_service import LiveRunData, WorldData, Event, ContextEvent, User, RunData
from rsg.rsg_pb import RsgPb
from logger import setup_logger

logger = setup_logger(__name__)


class DescriptionGenerator(BaseDescriptionGenerator):
    def __init__(self, live_run: LiveRunData, world_data: WorldData, video_path: Path, rsg_pb: RsgPb):
        self._live_run = live_run
        self._world_data = world_data
        self._video_path = video_path
        self.rsg_pb = rsg_pb
        super().__init__(video_path=video_path)

        self.sub_template = Template(inspect.cleandoc("""        

            ■ 分段详情
            $timelines_info

            ■ 个人最佳
            $pb_info

        """))


    def _generate_timelines_info(self):
        def event_to_str(event: Event) -> str:
            event_str = f"{util.ts_to_str_sec(event.igt)} {translator.event_map[event.eventId]}"
            if config.use_rsg_pb and self.rsg_pb.is_pb(event):
                event_str += " pb"
            return event_str

        event_list = self._live_run.eventList
        return " || ".join(list(map(event_to_str, event_list)))

    def _generate_pb_info(self):
        if not config.use_rsg_pb:
            return None
        def get_pb_str(key):
            if not self.rsg_pb.pb_info[key].igt:
                return ""
            pb_time = datetime.fromtimestamp(self.rsg_pb.pb_info[key].time).strftime("%Y-%m-%d")
            pb_str = (f"·{translator.event_map[key]}\t{util.ts_to_str(self.rsg_pb.pb_info[key].igt)}"
                      f" | {pb_time}"
                      f" | 距今 {int((time.time() - self.rsg_pb.pb_info[key].time) / (60 * 60 * 24))} 天"
                      f" | 链接：{self.rsg_pb.pb_info[key].bvid or '无'}")
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
                              f"{translator.event_map[key]}")
            i += 1
        upload_reason += " | ".join(upload_setting_list)
        upload_reason += "\n本场速通满足：\n"

        upload_reason_list = []
        i = 0
        for event in self._live_run.eventList:
            if event.igt < config.upload_setting.rsg[event.eventId]:
                upload_reason_list.append(f"{CIRCLE_NUMBERS[i]} sub"
                                          f"{util.ts_to_str_sec(config.upload_setting.rsg[event.eventId])} "
                                          f"{translator.event_map[event.eventId]}")
                i += 1
        upload_reason += " | ".join(upload_reason_list)
        return upload_reason


    def generate_about_info(self):
        return inspect.cleandoc(f"""

            · paceman：https://paceman.gg/stats/run/{self._world_data.data.id}/
            · api：https://paceman.gg/stats/api/getWorld/?worldId={self._world_data.data.id}

        """)

    def generate_sub_template(self) -> str:
        return self.sub_template.safe_substitute(
            timelines_info=self._generate_timelines_info(),
            pb_info=self._generate_pb_info() or "无",
        )

    def get_desc_path(self) -> Path:
        return config.rsg_video_dir / f'desc[{self._world_data.data.id}].txt'


if __name__ == '__main__':

    _desc_generator = DescriptionGenerator(
        live_run=LiveRunData(
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
            contextEventList=[
                ContextEvent(
                    eventId="rsg.obtain_iron_ingot",
                    rta=20567,
                    igt=18952
                ),
                ContextEvent(
                    eventId="rsg.obtain_iron_pickaxe",
                    rta=67713,
                    igt=66123
                ),
                ContextEvent(
                    eventId="rsg.obtain_lava_bucket",
                    rta=184160,
                    igt=182573
                ),
                ContextEvent(
                    eventId="rsg.obtain_crying_obsidian",
                    rta=300013,
                    igt=292775
                ),
                ContextEvent(
                    eventId="rsg.obtain_obsidian",
                    rta=300013,
                    igt=292775
                ),
                ContextEvent(
                    eventId="rsg.loot_bastion",
                    rta=377213,
                    igt=366075
                ),
                ContextEvent(
                    eventId="rsg.obtain_blaze_rod",
                    rta=616613,
                    igt=604475
                )
            ],
            user=User(
                uuid="8ee48ee6-7cfe-495a-8051-40d7a31ebb91",
                liveAccount=None
            ),
            isCheated=False,
            isHidden=False,
            numLeaves=0,
            lastUpdated=1753606925065,
            itemData=None,
            nickname="Wojcio234"
        ),
        world_data=WorldData(data=RunData(id=0, worldId="", nickname="", uuid="", insertTime=0, updateTime=0), time=0, isLive=False),
        video_path=Path(r"D:\视频\ranked\20260122\match[5330969].mp4"),
        rsg_pb=RsgPb()
    )

    print(_desc_generator.generate())
