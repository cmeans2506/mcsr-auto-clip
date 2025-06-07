from pathlib import Path
from datetime import datetime
import time
from typing import Optional

from config import config
from translator import translator
import util
from ffmpeg_service import ffmpeg_service
from rsg.paceman_service import LiveRunData, WorldData, Event
from rsg.rsg_pb import rsg_pb

class DescriptionGenerator:
    def __init__(self, live_run: LiveRunData, world_data: WorldData, video_path: Path):
        self._live_run = live_run
        self._world_data = world_data
        self._video_path = video_path

        self._video_info = ffmpeg_service.get_video_info(self._video_path)

    def _generate_timelines_info(self):
        def event_to_str(event: Event) -> str:
            event_str = f"{util.ts_to_str(event.igt)}\t{translator.event_map[event.eventId]}"
            if rsg_pb.is_pb(event):
                event_str += " 个人最佳"
            return event_str

        event_list = self._live_run.eventList
        return "\n".join(list(map(event_to_str, event_list)))


    def _generate_pb_info(self):
        def get_pb_str(key):
            pb_time = datetime.fromtimestamp(rsg_pb.pb_info[key]['time']).strftime("%Y-%m-%d")
            pb_str = (f"·{translator.event_map[key]}\n{util.ts_to_str(rsg_pb.pb_info[key]['igt'])}"
                      f" | {pb_time}"
                      f" | 距今{int((time.time() - rsg_pb.pb_info[key]['time']) / (60 * 60 * 24))}天"
                      f" | 链接：{rsg_pb.pb_info[key]['bvid']}")
            return pb_str

        return "\n".join(list(map(get_pb_str, rsg_pb.pb_info)))


    def _generate_upload_reason(self):
        CIRCLE_NUMBERS = "①②③④⑤⑥⑦⑧⑨⑩"
        i = 0
        upload_reason = ""
        upload_setting_list = []
        for key in config.upload_setting.rsg:
            # 时间设为 0 表示忽略
            if config.upload_setting.rsg[key] == 0:
                continue
            upload_setting_list.append(f"{CIRCLE_NUMBERS[i]}sub"
                              f"{util.ts_to_str(config.upload_setting.rsg[key])}"
                              f"{translator.event_map[key]}")
            i += 1
        upload_reason += " ".join(upload_setting_list)
        upload_reason += "\n本场速通满足：\n"

        upload_reason_list = []
        i = 0
        for event in self._live_run.eventList:
            if event.igt < config.upload_setting.rsg[event.eventId]:
                upload_reason_list.append(f"{CIRCLE_NUMBERS[i]}sub"
                                  f"{util.ts_to_str(config.upload_setting.rsg[event.eventId])}"
                                  f"{translator.event_map[event.eventId]}")
                i += 1
        upload_reason += " | ".join(upload_reason_list)
        return upload_reason

    def _generate_about_info(self):
        return f""" · 本场速通详细信息：https://paceman.gg/stats/run/{self._world_data.data.id}/
 · 更多详情：https://paceman.gg/stats/api/getWorld/?worldId={self._world_data.data.id}"""

    def _generate_video_info(self):
        return f"""宽度：{self._video_info.width}
高度：{self._video_info.height}
帧率：{self._video_info.frame_rate}
码率：{int(self._video_info.bit_rate / 1024)}kbps
文件大小：{int(self._video_info.size / (1024 * 1024))}MB
编码器类型：{self._video_info.codec_long_name}"""

    def _generate_repository_info(self):
        return """MCSR AUTO CLIP by @-Cmeans- (https://b23.tv/VyvEo6u) 
开源地址：https://github.com/cmeans2506/mcsr-auto-clip
"""

    def generate_video_desc(self):
        desc = f"""本视频为自动投稿
{'大会员请开4K' if self._video_info.height > 1600 else ''}

■ 分段详情：
{self._generate_timelines_info()}

■ 个人最佳：
{self._generate_pb_info()}

■ 投稿条件：
{self._generate_upload_reason()}

■ 相关链接：
{self._generate_about_info()}

■ 视频信息：
{self._generate_video_info()}

■ 项目信息：
{self._generate_repository_info()}
"""
        with open(config.video_dir / f'desc world[{self._world_data.data.id}].txt', 'w', encoding="utf8") as desc_file:
            desc_file.write(desc)
        return desc
