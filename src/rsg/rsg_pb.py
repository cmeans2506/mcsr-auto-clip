import json
import time
import threading
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal

from pydantic import BaseModel

import util
from rsg.paceman_service import Event, LiveRunData, EventIdType
from bilibili_uploader import BiliUploader
from config import config, config_dir
from logger import setup_logger

logger = setup_logger(__name__)


class RsgPbSignalHub(QObject):
    rsg_pb_signal = pyqtSignal()

rsg_pb_signal_hub = RsgPbSignalHub()

RSG_PB_EVENT_ID = frozenset({"rsg.first_portal", "rsg.enter_stronghold", "rsg.enter_end", "rsg.credits"})

class Record(BaseModel):
    id: int = 0
    igt: int = 0
    bvid: Optional[str] = None
    time: int = 0

class RecordJsonSerilize(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Record):
            return Record.model_dump(o, mode='json')
        else:
            return json.JSONEncoder.default(self, o)  #如果不是上述类型，就按照json默认序列化方式操作

class RsgPb:
    def __init__(self):
        self.pb_info: dict[EventIdType, Record] = {
            EventIdType.FIRST_PORTAL: Record(),
            EventIdType.ENTER_STRONGHOLD: Record(),
            EventIdType.ENTER_END: Record(),
            EventIdType.FINISH: Record()
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
                        logger.warning(f"pb.json: Missing keys: {missing}. Filling with default values.")
                    if extra:
                        logger.warning(f"pb.json: Extra keys found: {extra}.")

    def is_pb(self, event: Event) -> bool:
        if self.pb_info.get(event.eventId) is None:
            return False

        return event.igt < self.pb_info[event.eventId].igt

    def write_back(self):
        with open(self.pb_file_path, "w", encoding="utf8") as pb_file:
            json.dump(self.pb_info, pb_file, indent=4, cls=RecordJsonSerilize)


    def check_for_pb(self, bili_uploader: BiliUploader, live_run: LiveRunData):
        UPLOAD_TIMEOUT = 600
        pb_events = [event for event in live_run.eventList if self.is_pb(event)]

        if not pb_events:
            logger.info(f"Live run {live_run.id} is not PB for any events.")
            return

        def get_bvid() -> str | None:
            if not config.use_upload:
                logger.info("Upload feature disabled. The new PB record will not contain video link.")
                return None

            if not bili_uploader.rsg_pb_check_event.wait(timeout=UPLOAD_TIMEOUT):
                logger.warning(f"Upload did not complete within {UPLOAD_TIMEOUT}s. "
                               f"The new PB record will not contain video link.")
                return None

            return bili_uploader.get_latest_upload_history().bvid

        def job():
            bvid = get_bvid()
            now = int(time.time())

            for event in pb_events:
                self.pb_info[event.eventId] = Record(id=live_run.id, igt=event.igt, bvid=bvid, time=now)

            self.write_back()

            rsg_pb_signal_hub.rsg_pb_signal.emit()

        threading.Thread(
            target=job,
            name=f"check_for_pb_{live_run.id}",
            daemon=True,
        ).start()

    def get_pb_summary(self):
        """获取PB摘要信息(用于显示)"""
        summary = []

        for event_id, record in self.pb_info:
            if record.bvid and record.igt > 0:
                igt_str = util.ts_to_str(record.igt)
                timestamp = record.time
                date_str = f"{timestamp:%Y-%m-%d}" if timestamp > 0 else "unknown date"

                summary.append(f"{event_id}: {igt_str} - {record.bvid} ({date_str})")

        return ', '.join(summary) if summary else "No pb records"


# rsg_pb = RsgPb() if config.use_rsg_pb else None
