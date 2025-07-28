from typing import Optional, Literal, Any
from pydantic import BaseModel, computed_field
import requests
import time

import util
from util import find_first
from config import config


EventId = Literal["rsg.enter_nether", "rsg.enter_bastion","rsg.enter_fortress", "rsg.first_portal",
"rsg.second_portal", "rsg.enter_stronghold", "rsg.enter_end", "rsg.credits"]


class ContextEvent(BaseModel):
    eventId: str
    rta: int
    igt: int


class Event(BaseModel):
    eventId: EventId
    rta: int
    igt: int
    def is_valid_for_upload(self) -> bool:
        if config.upload_setting.rsg.get(self.eventId) is None:
            return False
        return self.igt < config.upload_setting.rsg[self.eventId]

    def get_igt(self) -> int:
        return self.igt

class User(BaseModel):
    uuid: str
    liveAccount: Optional[str] = None

class ItemData(BaseModel):
    estimatedCounts: dict[str, int]
    usages: dict[str, int]


class LiveRunData(BaseModel):
    worldId: str
    gameVersion: str
    eventList: list[Event]
    contextEventList: list[ContextEvent]
    user: User
    isCheated: bool
    isHidden: bool
    numLeaves: int
    lastUpdated: int
    itemData: Optional[ItemData] = None
    nickname: str

    @computed_field
    @property
    def rta(self) -> int:
        # lastUpdated字段的值仅和eventList中的数据有关，与contextEventList无关
        return int(time.time() - self.lastUpdated // 1000 + self.eventList[-1].rta // 1000)

    def get_points(self) -> Optional[float]:
        if self.eventList[-1].eventId != "rsg.credits":
            return None
        # 总完成时间（秒）
        total_seconds = self.eventList[-1].igt // 1000
        # 计算分钟和秒钟
        minutes = int(total_seconds // 60)  # 整分钟数
        seconds = total_seconds % 60  # 剩余秒数
        # 计算积分
        points = 20 - (minutes + seconds / 100)
        return round(points, 2)

    def is_valid_for_clip(self) -> bool:
        for event in self.eventList:
            if event.igt < config.clip_setting.rsg[event.eventId]:
                return True
        return False

    def is_valid_for_upload(self) -> bool:
        for event in self.eventList:
            if event.igt < config.upload_setting.rsg[event.eventId]:
                # 只进fort,不算
                if event.eventId == 'rsg.enter_fortress':
                    if util.find_first(lambda e: e.eventId == 'rsg.enter_bastion', self.eventList) is None:
                        return False
                return True
        return False

    def model_post_init(self, context: Any, /) -> None:
        self.clean()

    def clean(self):
        """
        eventList 中存在 `rsg.second_portal` 这一项，我们不使用，将其清除
        :return: None
        """
        if util.find_first(lambda e: e.eventId == 'rsg.second_portal', self.eventList) is None:
            return
        if self.eventList[-1].eventId == 'rsg.second_portal':
            self.lastUpdated -= self.eventList[-1].rta - self.eventList[-2].rta
        self.eventList = list(filter(lambda e: e.eventId != 'rsg.second_portal', self.eventList))

    def is_complete_run(self) -> bool:
        return util.find_first(lambda e: e.eventId == "rsg.credits", self.eventList) is not None
"""
{
  "data": {
    "id": 303111,
    "worldId": "31aad8ee0540af3a0573ac959e85f8b81f3941010d8cd20a33b67d04b29a0237",
    "nickname": "dfanm",
    "uuid": "4990072b-252e-42f2-aef9-45cd765f2425",
    "twitch": "dfanm",
    "nether": 146952,
    "bastion": 200037,
    "fortress": null,
    "first_portal": null,
    "stronghold": null,
    "end": null,
    "finish": null,
    "netherRta": 152614,
    "bastionRta": 211353,
    "fortressRta": null,
    "first_portalRta": null,
    "strongholdRta": null,
    "endRta": null,
    "finishRta": null,
    "insertTime": 1715824742,
    "updateTime": 1715824799,
    "realUpdate": null,
    "vodId": 2146675569,
    "vodOffset": 14503
  },
  "time": 1748327006553,
  "isLive": false
}"""


class RunData(BaseModel):
    id: int
    worldId: str
    nickname: str
    uuid: str
    twitch: Optional[str] = None
    nether:  Optional[int] = None
    bastion: Optional[int] = None
    fortress: Optional[int] = None
    first_portal: Optional[int] = None
    stronghold: Optional[int] = None
    end: Optional[int] = None
    finish: Optional[int] = None
    netherRta:  Optional[int] = None
    bastionRta:  Optional[int] = None
    fortressRta: Optional[int] = None
    first_portalRta: Optional[int] = None
    strongholdRta: Optional[int] = None
    endRta: Optional[int] = None
    finishRta: Optional[int] = None
    insertTime: int
    updateTime: int
    realUpdate: Optional[int] = None
    vodId: Optional[int] = None
    vodOffset: Optional[int] = None

class WorldData(BaseModel):
    data: RunData
    time: int  # 时间戳（毫秒）
    isLive: bool



class PacemanService:
    _LIVE_RUNS_API = "https://paceman.gg/api/ars/liveruns"

    _GET_WORLD_API = "https://paceman.gg/stats/api/getWorld"

    def __init__(self):
        self._clip_worlds: list[str] = []
        self._last_live_run: Optional[LiveRunData] = None
        # 有关uuid和name的检查在 RankedService 的初始化过程中已经检查过了
        # 这里就不再重复检查了

    def get_live_runs(self) -> list[LiveRunData]:
        try:
            data = requests.get(self._LIVE_RUNS_API).json()
        except requests.exceptions.RequestException as e:
            print(f"请求：{e.request.url}时出现错误，如果频繁出现此提示，请检查你的网络")
            return []

        return [LiveRunData(**live_run) for live_run in data]

    def get_my_live_run(self) -> Optional[LiveRunData]:
        live_runs = self.get_live_runs()

        def is_my_live_run(world_data: LiveRunData) -> bool:
            return world_data.nickname == config.player.name and not world_data.isCheated and not world_data.isHidden

        return find_first(is_my_live_run, live_runs)


    def get_latest_run(self) -> Optional[LiveRunData]:
        """
        返回最新一场的 live run 信息
        :return: LiveRunData
        """
        live_run = self.get_my_live_run()
        print("当前live_run信息", live_run)
        run = None

        # 总共两种情况：①非完整速通，即一场速通没有完成就reset，但是这场速通中有值得切片的pace
        #             此时对应_last_live_run为非空，live_run为空
        #             ②完整速通，由于paceman网站的live api会将完整速通的数据保留5分钟才消失，时间过长
        #             因此不等待live_run变为空就返回数据

        if self._last_live_run is not None and live_run is None:
            run = self._last_live_run
        elif self._last_live_run is not None and live_run is not None:
            if live_run.eventList[-1].eventId == "rsg.credits":
                run = live_run
        self._last_live_run = live_run

        if run is None:
            return None

        if not run.is_valid_for_clip():
            print(run, "不满足切片条件，跳过")
            return None
        if run.worldId in self._clip_worlds:
            print(run, "已经切片过，跳过")
            return None

        self._clip_worlds.append(run.worldId)
        return run


    def get_world(self, world_id: str) -> Optional[WorldData]:
        try:
            data = requests.get(f"{self._GET_WORLD_API}/?worldId={world_id}").json()
        except requests.exceptions.RequestException as e:
            print(f"请求：{e.request.url}时出现错误，如果频繁出现此提示，请检查你的网络")
            return None

        return WorldData(**data)

paceman_service = PacemanService()