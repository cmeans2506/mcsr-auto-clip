import json
from pathlib import Path
import time
import threading
from pydantic import BaseModel

import util
from rsg.paceman_service import Event, LiveRunData, WorldData, EventId
from bilibili_uploader import BiliUploader
from config import config, config_dir
from logger import setup_logger

logger = setup_logger(__name__)

RSG_PB_EVENT_ID = frozenset({"rsg.first_portal", "rsg.enter_stronghold", "rsg.enter_end", "rsg.credits"})

class Record(BaseModel):
    id: int = 0
    igt: int = 0
    bvid: str = ""
    time: int = 0

class RecordJsonSerilize(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Record):
            return Record.model_dump(o, mode='json')
        else:
            return json.JSONEncoder.default(self, o)  #如果不是上述类型，就按照json默认序列化方式操作

class RsgPb:
    def __init__(self):
        self.pb_info: dict[EventId, Record] = {
            "rsg.first_portal": Record(),
            "rsg.enter_stronghold": Record(),
            "rsg.enter_end": Record(),
            "rsg.credits": Record()
        }
        self.pb_file_path = config_dir / "pb.json"
        if self.pb_file_path.exists():
            with open(self.pb_file_path, "r", encoding="utf8") as pb_file:
                raw_data = json.load(pb_file)

                for event_id, record_data in raw_data.items():
                    if event_id in RSG_PB_EVENT_ID:
                        self.pb_info[event_id] = Record(**record_data)

                loaded_keys = set(raw_data.keys())
                if loaded_keys != RSG_PB_EVENT_ID:
                    missing = RSG_PB_EVENT_ID - loaded_keys
                    extra = loaded_keys - RSG_PB_EVENT_ID
                    if missing:
                        logger.warning(f"pb.json: 缺失键: {missing}，用默认值填充")
                    if extra:
                        logger.warning(f"pb.json: 多余的键: {extra}")

    def is_pb(self, event: Event) -> bool:
        if self.pb_info.get(event.eventId) is None:
            return False

        return event.igt < self.pb_info[event.eventId].igt

    def write_back(self):
        with open(self.pb_file_path, "w", encoding="utf8") as pb_file:
            json.dump(self.pb_info, pb_file, indent=4, cls=RecordJsonSerilize)

    def check_for_pb(self, bili_uploader: BiliUploader, live_run: LiveRunData, world_data: WorldData):
        if not config.use_upload:
            logger.info("未启用上传功能，跳过pb更新检查")
            return
        wait_for_upload = 600
        def job():
            if not bili_uploader.rsg_pb_check_event.wait(timeout=wait_for_upload):
                logger.warning(f"未在{wait_for_upload}秒内完成上传，放弃pb更新检查")

            up_history = bili_uploader.get_latest_upload_history()

            now = int(time.time())
            for event in live_run.eventList:
                if self.is_pb(event):
                    self.pb_info[event.eventId].id = world_data.data.id
                    self.pb_info[event.eventId].igt = event.igt
                    self.pb_info[event.eventId].bvid = up_history.bvid
                    self.pb_info[event.eventId].time = now
            self.write_back()

        thread = threading.Thread(
            target=job,
            args=(),
            name=f"check_for_pb {world_data.data.id}",
            daemon=True
        )
        thread.start()

    def get_pb_summary(self):
        """获取PB摘要信息(用于显示)"""
        summary = []

        for event_id, record in self.pb_info:
            if record.bvid and record.igt > 0:
                igt_str = util.ts_to_str(record.igt)
                timestamp = record.time
                date_str = f"{timestamp:%Y-%m-%d}" if timestamp > 0 else "未知日期"

                summary.append(f"{event_id}: {igt_str} - {record.bvid} ({date_str})")

        return ', '.join(summary) if summary else "暂无PB记录"


# rsg_pb = RsgPb() if config.use_rsg_pb else None
