from typing import Optional, Any
from pathlib import Path

from base.base_cover_generator import BaseCoverGenerator
from rsg.paceman_service import WorldData, LiveRunData, Event, PacemanService
import util
from config import config
from translator import translator
from rsg.rsg_pb import RsgPb
from logger import setup_logger

logger = setup_logger(__name__)

class CoverGenerator(BaseCoverGenerator):
    _FINISH_IMAGE_PATH = config.template_dir / "image" / "Dragon_Egg.webp"
    _END_IMAGE_PATH = config.template_dir / "image" / "End_Stone.webp"
    _STRONGHOLD_IMAGE_PATH = config.template_dir / "image" / "Mossy_Stone_Bricks.webp"
    _FIRST_PORTAL_IMAGE_PATH = config.template_dir / "image" / "Eye_of_Ender.webp"

    _FONT_PATH = config.template_dir / "fonts" / "JiangChengLvDongHei.mcsrsubset.woff2"

    def __init__(self, live_run: LiveRunData, world_data: WorldData, video_path: Path, rsg_pb: RsgPb):
        self._live_run = live_run
        self._world_data = world_data
        self._video_path = video_path
        self.rsg_pb = rsg_pb
        super().__init__(video_path=video_path)


    def get_image_src(self):
        image_src_dict = {
            "rsg.credits": self._FINISH_IMAGE_PATH,
            "rsg.enter_end": self._END_IMAGE_PATH,
            "rsg.enter_stronghold": self._STRONGHOLD_IMAGE_PATH,
            "rsg.first_portal": self._FIRST_PORTAL_IMAGE_PATH
        }
        return image_src_dict.get(self._live_run.eventList[-1].eventId, self._FINISH_IMAGE_PATH)


    def generate_event_str_list(self) -> list[str]:
        def get_event_str(event: Event):
            event_str = f"{util.ts_to_str_sec(event.igt)}{translator.event_map[event.eventId]}"
            if config.use_rsg_pb and self.rsg_pb.is_pb(event):
                event_str += " PB"
            return event_str

        # 在event_list中，有若干rsg中的时间节点，例如盲传，进末地等
        # 在制作封面时，需要从这些时间节点中选择其中的三个用作展示
        # 为了选出相对“更有价值”的时间节点信息，我简单设计了一个算法
        # 主要逻辑是根据当前节点是否是pb，当前节点是否符合投稿时间要求来决定先后次序
        # 除此之外还手动指定了这些时间节点的先后顺序，当两个时间节点同时满足或者不满足上述的条件时，手动指定的顺序发挥作用
        # 这里我想到了两种实现方式：①手动编写lambda函数，直接比较两个节点谁“更有价值”
        #                      ②加权计算
        # 第一种方法我总觉得太绕，这里就用第二种方法写了

        def calculate_event_priority_score(event: Event):
            inner_html_order = ["rsg.credits", "rsg.first_portal", "rsg.enter_nether", "rsg.enter_end",
                                "rsg.enter_stronghold", "rsg.second_portal", "rsg.enter_fortress", "rsg.enter_bastion"]
            inner_html_map = {element: i for i, element in enumerate(inner_html_order)}
            base_priority = inner_html_map[event.eventId]
            pb_penalty = 0 if config.use_rsg_pb and self.rsg_pb.is_pb(event) else 100
            upload_penalty = 0 if event.is_valid_for_upload() else 100
            return base_priority + pb_penalty + upload_penalty

        event_list = sorted(self._live_run.eventList, key=calculate_event_priority_score)
        # 只选择 3 个 event 进行展示
        event_list = event_list[:3]
        # 按照时间升序排序
        event_list.sort(key=Event.get_igt)
        return list(map(get_event_str, event_list))


    def get_template_file_path(self) -> Path:
        return config.template_dir / "cover_for_rsg.html"

    def get_bg_path(self) -> Path:
        return config.rsg_video_dir / f'bg[{self._world_data.data.id}].webp'

    def get_render_data(self) -> dict[str, Any]:
        image_src = self.get_image_src()
        # 进入末地和隔墙有眼使用的图片是方块的图片，尺寸更大，CSS样式略有不同
        is_bigger_image = image_src == self._END_IMAGE_PATH or image_src == self._STRONGHOLD_IMAGE_PATH
        event_str_list = self.generate_event_str_list()
        points = self._live_run.get_points()
        return{
            'font_path': self.get_base64(self._FONT_PATH),
            'bg_path': self.get_base64(self.get_bg_path()),
            'world_data': self._world_data.model_dump(),
            'is_bigger_image': is_bigger_image,
            'event_str_list': event_str_list,
            'corner_image_src': self.get_base64(image_src),
            'points': points,
        }

    def get_save_path(self) -> Path:
        return config.rsg_video_dir / f'cover[{self._world_data.data.id}].jpg'

    def get_html_path(self) -> Path:
        return config.rsg_video_dir / f'cover[{self._world_data.data.id}].html'


def main():
    paceman_service = PacemanService()

    live = paceman_service.get_live_runs()[-1]
    world_data = paceman_service.get_world(live.worldId)
    rsg_pb = RsgPb()
    cover_generator = CoverGenerator(video_path=Path(r"D:\视频\ranked\20260122\match[5330969].mp4"), live_run=live,
                             world_data=world_data, rsg_pb=rsg_pb)
    cover_generator.generate()

if __name__ == "__main__":
    main()

