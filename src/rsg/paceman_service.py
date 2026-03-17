from functools import cache
from typing import Optional, Literal, Any
from pydantic import BaseModel, computed_field
import requests
import time

from mcsr_enums import EventIdType
import util
from util import find_first
from config import config
from my_exceptions import PacemanAPIUnavailableError
from logger import setup_logger

logger = setup_logger(__name__)


class Event(BaseModel):
    eventId: EventIdType
    rta: int
    igt: int
    def is_valid_for_upload(self) -> bool:
        if config.upload_setting.rsg.get(self.eventId) is None:
            return False
        return self.igt < config.upload_setting.rsg[self.eventId]

    def get_igt(self) -> int:
        return self.igt

    def __str__(self):
        return f"{util.ts_to_str_sec(self.igt)}{self.eventId.label}"

class User(BaseModel):
    uuid: str


class LiveRunData(BaseModel):
    id: int = 0
    worldId: str
    gameVersion: str
    eventList: list[Event]
    user: User
    isCheated: bool
    isHidden: bool
    lastUpdated: int
    nickname: str

    def __str__(self):
        eventList_str = ' '.join([str(e) for e in self.eventList])
        return f"{self.gameVersion} | {self.nickname} | {eventList_str}"

    @computed_field
    @property
    def rta(self) -> int:
        # lastUpdated字段的值仅和eventList中的数据有关，与contextEventList无关
        return int(time.time() - self.lastUpdated // 1000 + self.eventList[-1].rta // 1000)

    @property
    def is_valid_for_clip(self) -> bool:
        for event in self.eventList:
            if event.igt < config.clip_setting.rsg[event.eventId]:
                return True
        return False

    @property
    def is_valid_for_upload(self) -> bool:
        for event in self.eventList:
            if event.igt < config.upload_setting.rsg[event.eventId]:
                # 只进fort,不算
                if event.eventId == EventIdType.ENTER_FORTRESS:
                    if util.find_first(lambda e: e.eventId == EventIdType.ENTER_BASTION, self.eventList) is None:
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
        if util.find_first(lambda e: e.eventId == EventIdType.SECOND_PORTAL, self.eventList) is None:
            return
        if self.eventList[-1].eventId == EventIdType.SECOND_PORTAL:
            self.lastUpdated -= self.eventList[-1].rta - self.eventList[-2].rta
        self.eventList = list(filter(lambda e: e.eventId != EventIdType.SECOND_PORTAL, self.eventList))


    @property
    def is_complete_run(self) -> bool:
        return self.eventList[-1].eventId == EventIdType.FINISH


class PacemanService:
    _LIVE_RUNS_API = "https://paceman.gg/api/ars/liveruns"

    _GET_WORLD_API = "https://paceman.gg/stats/api/getWorld"

    def __init__(self):
        self._clip_worlds: list[str] = []
        self._last_live_run: Optional[LiveRunData] = None
        # 有关uuid和name的检查在 RankedService 的初始化过程中已经检查过了
        # 这里就不再重复检查了
        self._session = requests.Session()

    def get_live_runs(self) -> list[LiveRunData]:
        try:
            data = self._session.get(self._LIVE_RUNS_API).json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error requesting {e.request.url}. If this persists, please check your network connection.")
            return []

        return [LiveRunData(**live_run) for live_run in data]

    def get_my_live_run(self) -> Optional[LiveRunData]:
        live_runs = self.get_live_runs()

        def is_my_live_run(world_data: LiveRunData) -> bool:
            uuid_without_hyphen = world_data.user.uuid.replace("-", "")
            return uuid_without_hyphen == config.player.uuid and not world_data.isCheated and not world_data.isHidden

        return find_first(is_my_live_run, live_runs)


    def get_latest_run(self) -> Optional[LiveRunData]:
        """
        返回最新一场的 live run 信息
        :return: LiveRunData
        """
        if not config.rsg_job:
            return None
        live_run = self.get_my_live_run()
        self.update_id(live_run)
        logger.info(f"Live speedrun data: {live_run}")
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

        if not run.is_valid_for_clip:
            logger.info("Clip conditions not met. Skipping.")
            return None
        if run.worldId in self._clip_worlds:
            logger.info("World has already been clipped. Skipping.")
            return None

        self._clip_worlds.append(run.worldId)
        return run


    @cache
    def get_id_by_uuid(self, world_id: str) -> int:
        resp = self._session.get(f"{self._GET_WORLD_API}/?worldId={world_id}")
        resp.raise_for_status()
        id_ = resp.json()["data"]["id"]
        logger.info(f"Get id {id_} for run {world_id}.")
        return id_

    def update_id(self, live_run: LiveRunData):
        try:
            live_run.id = self.get_id_by_uuid(live_run.worldId)
        except:
            return
