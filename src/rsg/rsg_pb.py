import json
from pathlib import Path
import time
import threading

from rsg.paceman_service import Event, paceman_service, LiveRunData, WorldData, EventId
from bilibili_uploader import bilibili_uploader
from pydantic import BaseModel


class Record(BaseModel):
    id: int
    igt: int
    bvid: str
    time: int


class RsgPb:
    def __init__(self):
        with open(Path(__file__).parent.parent.parent / "config" / "pb.json", "r", encoding="utf8") as pb_file:
            self.pb_info: dict[EventId, Record] = json.load(pb_file)

    def is_pb(self, event: Event) -> bool:
        if self.pb_info.get(event.eventId) is None:
            return False

        return event.igt < self.pb_info[event.eventId]['igt']

    def write_back(self):
        with open(Path(__file__).parent.parent.parent / "config" / "pb.json", "w", encoding="utf8") as pb_file:
            json.dump(self.pb_info, pb_file, indent=4)

    def check_for_pb(self, live_run: LiveRunData, world_data: WorldData):
        def job():
            while 1:
                if (up_history := bilibili_uploader.get_upload_history_by_id(world_data.data.id)) is not None:
                    break
                time.sleep(20)

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

rsg_pb = RsgPb()

