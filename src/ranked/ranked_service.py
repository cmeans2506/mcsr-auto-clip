from typing import Optional
from pydantic import BaseModel, Field
import requests
from enum import Enum
from datetime import datetime

from config import config
import util as util
from translator import translator
from my_exceptions import PlayerNotFoundException, RankedAPIUnavailableError
from logger import setup_logger

logger = setup_logger(__name__)


class Seed(BaseModel):
    # 使用未筛选的种子，以下字段都为null或[]
    id_: Optional[str] = Field(alias='id')
    overworld: Optional[str]
    nether: Optional[str]
    endTowers: Optional[list[int]]
    variations: Optional[list[str]]


class Player(BaseModel):
    uuid: str
    nickname: str
    roleType: int
    eloRate: Optional[int]
    eloRank: Optional[int]
    country: Optional[str]


class Result(BaseModel):
    uuid: Optional[str] = None
    time: int


class Change(BaseModel):
    uuid: str
    change: Optional[int]
    eloRate: Optional[int]


class Rank(BaseModel):
    season: Optional[int] = None
    allTime: Optional[int] = None

class MatchType(Enum):
    CASUAL_MATCH = 1
    RANKED_MATCH = 2
    PRIVATE_ROOM_MATCH = 3
    EVNET_MODE_MATCH = 4

# MatchInfo 是简化版的比赛信息，后面的 MatchData 是详细的
class MatchInfo(BaseModel):


    id_: int = Field(alias='id')
    type_: MatchType = Field(alias='type')
    seed: Seed
    category: Optional[str]
    gameMode: Optional[str] = None
    players: list[Player]
    spectators: list[Player]
    result: Result
    forfeited: bool
    decayed: bool
    rank: Rank
    changes: list[Change]
    season: int
    date: int
    seedType: Optional[str]
    bastionType: Optional[str]
    tag: Optional[str] = None

    def get_opponent_info(self) -> Player:
        return next(filter(lambda player_info: player_info.uuid != config.player.uuid, self.players), None)
    def get_my_info(self) -> Player:
        return next(filter(lambda player_info: player_info.uuid == config.player.uuid, self.players), None)

    def is_valid_for_upload(self) -> bool:
        if self.result.time > config.upload_setting.ranked[self.type_.name].max_time:
            return False
        if self.bastionType not in config.upload_setting.ranked[self.type_.name].bastion_type:
            return False
        if self.seedType not in config.upload_setting.ranked[self.type_.name].seed_type:
            return False
        return True

    def __str__(self) -> str:
        mode = translator.match_type_map[self.type_.name]

        my_info = self.get_my_info()
        if my_info and my_info.uuid == self.result.uuid:
            result = "胜"
        else:
            result = "负"

        if self.forfeited:
            time_part = "弃赛"
        elif result == "胜":
            time_part = util.ts_to_str(self.result.time)
        else:
            time_part = "-"

        seed_type = translator.seedtype_map[self.seedType]

        current_time = datetime.now().timestamp()
        time_diff = current_time - self.date

        if time_diff < 3600:  # 小于1小时
            minutes_ago = int(time_diff / 60)
            time_diff_str = f"{minutes_ago}分钟前"
        elif time_diff < 86400:  # 小于1天
            hours_ago = int(time_diff / 3600)
            time_diff_str = f"{hours_ago}小时前"
        else:  # 大于等于1天
            days_ago = int(time_diff / 86400)
            time_diff_str = f"{days_ago}天前"

        return f"{mode} - {result} {time_part} {seed_type} {time_diff_str}"


class UserData(BaseModel):
    class Achievements(BaseModel):
        class AchievementItem(BaseModel):
            id_: str = Field(alias='id')
            date: int
            data: list
            level: int
            goal: Optional[int] = None

        display: list[AchievementItem]
        total: list[AchievementItem]

    class Timestamp(BaseModel):
        firstOnline: int
        lastOnline: int
        lastRanked: int
        nextDecay: Optional[int]


    class Statistics(BaseModel):
        class StatisticsCategory(BaseModel):
            class RankedCasualStats(BaseModel):
                ranked: Optional[int] = None
                casual: Optional[int] = None

            bestTime: RankedCasualStats
            highestWinStreak: RankedCasualStats
            currentWinStreak: RankedCasualStats
            playedMatches: RankedCasualStats
            playtime: RankedCasualStats
            completionTime: RankedCasualStats
            forfeits: RankedCasualStats
            completions: RankedCasualStats
            wins: RankedCasualStats
            loses: RankedCasualStats

        season: StatisticsCategory
        total: StatisticsCategory

    class WeeklyRaces(BaseModel):
        id_: int = Field(alias='id')
        time: int
        rank: int

    class SeasonResult(BaseModel):
        class LastSeasonResult(BaseModel):
            eloRate: Optional[int]
            eloRank: Optional[int]
            phasePoint: int

        last: LastSeasonResult
        highest: Optional[int]
        lowest: Optional[int]
        phases: list

    uuid: str
    nickname: str
    roleType: int
    eloRate: Optional[int]
    eloRank: Optional[int]
    achievements: Achievements
    timestamp: Timestamp
    statistics: Statistics
    connections: dict
    weeklyRaces: list[WeeklyRaces]
    country: Optional[str]
    seasonResult: SeasonResult


class MatchData(BaseModel):
    class Timeline(BaseModel):
        uuid: str
        time: int
        type_: str = Field(alias="type")

    id_: int = Field(alias='id')
    type_: MatchType = Field(alias="type")
    seed: Seed
    category: str
    players: list[Player]
    spectators: list[Player]
    result: Result
    forfeited: bool
    decayed: bool
    rank: Rank
    changes: list[Change]
    completions: list[Result]
    timelines: list[Timeline]
    season: int
    date: int
    seedType: str
    bastionType: str
    tag: Optional[str] = None
    replayExist: bool

    def get_opponent_timeline(self, type_: str) -> Optional[Timeline]:
        return util.find_first(lambda timeline:timeline.type_ == type_
                                           and timeline.uuid != config.player.uuid, self.timelines)

    def get_player(self, uuid: str) -> Player:
        return util.find_first(lambda p:p.uuid == uuid, self.players)


class RankedService:
    _RANKED_API = "https://mcsrranked.com/api/users/"
    _MATCH_API = "https://mcsrranked.com/api/matches/"
    _MATCHES_API_EXTENSION = "/matches"

    def __init__(self):
        """

        :param name: 玩家名称
        :param uuid: 玩家的uuid
        """

        # try:
        #     logger.info("正在检验 'player.name' 和 'player.uuid' ")
        #     api = f"{RankedService._RANKED_API}{self._name}"
        #     response = requests.get(api)
        # except requests.exceptions.RequestException as e:
        #     logger.warning(f"请求：{e.request.url}时出现错误，请检查网络后重新启动")
        #     exit()
        # if response.status_code != 200:
        #     logger.warning(f"不存在玩家 '{name}' ，请检查 'player' 字段是否配置正确")
        #     exit()
        # if response.json()["data"]["uuid"] != uuid:
        #     logger.warning(f"在 'config.json' 中配置的 'player.uuid' 有误：{uuid}，"
        #           f"已修正为：{response.json()['data']['uuid']}")
        #     uuid = response.json()["data"]["uuid"]
        #
        # logger.info("'player.name' 和 'player.uuid' 检验通过！")

        self._any_clip_matches: list[int] = []
        self._death_clip_matches: list[int] = []
        self._session = requests.Session()

    @staticmethod
    def get_uuid(name: str) -> str:
        """
        请求错误：requests.exceptions.RequestException
        玩家不存在：requests.exceptions.HTTPError
        :param name:
        :return: uuid
        """
        logger.info(f"正在获取 {name} 的 uuid ")
        api = f"{RankedService._RANKED_API}{name}"
        try:
            response = requests.get(api)
            response.raise_for_status()
            return response.json()["data"]["uuid"]
        except requests.exceptions.HTTPError:
            logger.warning(f"不存在玩家 '{name}' ，请检查 'player' 字段是否配置正确")
            raise PlayerNotFoundException(name)
        except requests.exceptions.RequestException as e:
            logger.warning(f"请求：{e.request.url}时出现错误，请检查网络后重新启动")
            raise RankedAPIUnavailableError(api, e) from e



    def get_recent_matches(self, match_type: Optional[MatchType] = None, count: int = 50) -> list[MatchInfo]:
        api = f"{RankedService._RANKED_API}{config.player.name}{RankedService._MATCHES_API_EXTENSION}?count={count}"
        if match_type is not None:
            api += f"&type={match_type.value}"
        try:
            response = self._session.get(api)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError:
            logger.warning(f"不存在玩家 '{config.player.name}' ，请检查 'player' 字段是否配置正确")
            raise PlayerNotFoundException(config.player.name)
        except requests.exceptions.RequestException as e:
            if e.request:
                logger.warning(f"请求：{e.request.url}时出现错误，如果频繁出现此提示，请检查你的网络")
            return []

        return [MatchInfo(**match_info) for match_info in data["data"]]

    def get_latest_match(self) -> Optional[MatchInfo]:
        match_info_list = self.get_recent_matches(count=5)
        if not match_info_list:
            logger.info(f"{config.player.name}最近没有比赛")
            return None

        latest_match = match_info_list[0]
        logger.info(f"最新对局：{latest_match}")

        if latest_match.date < config.launch_time:
            logger.info("比赛时间早于脚本启动时间，跳过")
            return None
        if latest_match.result.uuid != config.player.uuid:
            logger.info("比赛未胜利，跳过")
            return None
        if latest_match.forfeited or latest_match.decayed:
            logger.info("不是完整比赛，跳过")
            return None
        if latest_match.result.time > config.clip_setting.ranked[latest_match.type_.name].max_time:
            logger.info(f"比赛的完成时间{util.ts_to_str(latest_match.result.time)}超过了最大允许时间"
                  f"{util.ts_to_str(config.clip_setting.ranked[latest_match.type_.name].max_time)}，跳过")
            return None
        if latest_match.bastionType not in config.clip_setting.ranked[latest_match.type_.name].bastion_type:
            logger.info(f"比赛的猪堡类型是{latest_match.bastionType}，不在指定的范围内："
                  f"{config.clip_setting.ranked[latest_match.type_.name].bastion_type}，跳过")
            return None
        if latest_match.seedType not in config.clip_setting.ranked[latest_match.type_.name].seed_type:
            logger.info(f"比赛的主世界类型是{latest_match.seedType}，不在指定的范围内："
                  f"{config.clip_setting.ranked[latest_match.type_.name].seed_type}，跳过")
            return None
        if latest_match.category != "ANY":
            logger.info(f"比赛的项目是{latest_match.category}，不是ANY%速通，跳过")
            return None
        if latest_match.id_ in self._any_clip_matches:
            logger.info(f"比赛已经被切片过，跳过")
            return None

        self._any_clip_matches.append(latest_match.id_)
        return latest_match

    def get_latest_death_match(self) -> Optional[MatchData]:
        match_info_list = self.get_recent_matches(count=5)
        if not match_info_list:
            return None

        latest_match = match_info_list[0]
        if latest_match.date < config.launch_time:
            return None
        if latest_match.id_ in self._death_clip_matches:
            return None

        latest_match_data = self.get_match_data(latest_match.id_)

        def is_death_timeline(timeline: MatchData.Timeline) -> bool:
            return timeline.type_ == "projectelo.timeline.death" and timeline.uuid == config.player.uuid
        if util.find_first(is_death_timeline, latest_match_data.timelines) is None:
            return None

        logger.info(f"最新死亡切片对局：match[{latest_match_data.id_}]")
        self._death_clip_matches.append(latest_match_data.id_)
        return latest_match_data


    def get_user_data(self) -> UserData:
        api = f"{RankedService._RANKED_API}{config.player.name}"
        return UserData(**(self._session.get(api).json()["data"]))

    def get_match_data(self, id_: int) -> MatchData:
        api = f"{RankedService._MATCH_API}{id_}"
        return MatchData(**(self._session.get(api).json()["data"]))


def main():
    ranked_service = RankedService()
    print(ranked_service.get_latest_match())
    print(ranked_service.get_user_data())
    print(ranked_service.get_match_data(1909310))

if __name__ == "__main__":
    main()