from typing import Optional
from pydantic import BaseModel, Field
import requests
from enum import Enum
from config import config
import util


class Seed(BaseModel):
    # 使用未筛选的种子，以下字段都为null或[]
    id_: Optional[str] = Field(alias='id')
    overworld: Optional[str]
    bastion: Optional[str]
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
    season: Optional[str] = None
    allTime: Optional[str] = None

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
    category: str
    gameMode: str
    players: list[Player]
    spectators: list[Player]
    result: Result
    forfeited: bool
    decayed: bool
    rank: Rank
    changes: list[Change]
    season: int
    date: int
    seedType: str
    bastionType: str
    tag: Optional[str] = None

    def get_opponent_info(self) -> Player:
        return next(filter(lambda player_info: player_info.uuid != config.player.uuid, self.players), None)
    def get_my_info(self) -> Player:
        return next(filter(lambda player_info: player_info.uuid == config.player.uuid, self.players), None)


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

    def __init__(self, name: str, uuid: str):
        """

        :param name: 玩家名称
        :param uuid: 玩家的uuid
        """
        self._name = name
        try:
            print("正在检验 'player.name' 和 'player.uuid' ")
            api = f"{RankedService._RANKED_API}{self._name}"
            responce = requests.get(api)
        except requests.exceptions.RequestException as e:
            print(f"请求：{e.request.url}时出现错误，请检查网络后重新启动")
            exit()
        if responce.status_code != 200:
            print(f"不存在玩家 '{name}' ，请检查 'player' 字段是否配置正确")
            exit()
        if responce.json()["data"]["uuid"] != uuid:
            print(f"在 'config.json' 中配置的 'player.uuid' 有误：{uuid}，"
                  f"已修正为：{responce.json()['data']['uuid']}")
            uuid = responce.json()["data"]["uuid"]

        print("'player.name' 和 'player.uuid' 检验通过！")

        self._uuid = uuid
        self._cliped_matches: list[int] = []

    def get_recent_matches(self, match_type: Optional[MatchType] = None, count: int = 50) -> list[MatchInfo]:
        api = f"{RankedService._RANKED_API}{self._name}{RankedService._MATCHES_API_EXTENSION}?count={count}"
        if match_type is not None:
            api += f"&type={match_type.value}"
        try:
            data = requests.get(api).json()
        except requests.exceptions.RequestException as e:
            print(f"请求：{e.request.url}时出现错误，如果频繁出现此提示，请检查你的网络")
            return []
        if data["status"] != "success":
            raise RuntimeError(data["data"])

        return [MatchInfo(**match_info) for match_info in data["data"]]

    def get_latest_match(self) -> Optional[MatchInfo]:
        match_info_list = self.get_recent_matches(count=5)
        if not match_info_list:
            return None

        latest_match = match_info_list[0]
        print(f"最新对局：{latest_match}")

        if latest_match.date < config.launch_time:
            print("比赛时间早于程序启动时间，跳过")
            return None
        if latest_match.result.uuid != config.player.uuid:
            print("比赛未胜利，跳过")
            return None
        if latest_match.forfeited or latest_match.decayed:
            print("不是完整比赛，跳过")
            return None
        if latest_match.result.time > config.clip_setting[latest_match.type_.name].max_time:
            print(f"比赛的完成时间{util.ts_to_str(latest_match.result.time)}超过了最大允许时间"
                  f"{util.ts_to_str(config.clip_setting[latest_match.type_.name].max_time)}，跳过")
            return None
        if latest_match.bastionType not in config.clip_setting[latest_match.type_.name].bastion_type:
            print(f"比赛的猪堡类型是{latest_match.bastionType}，不在指定的范围内："
                  f"{config.clip_setting[latest_match.type_.name].bastion_type}，跳过")
            return None
        if latest_match.seedType not in config.clip_setting[latest_match.type_.name].seed_type:
            print(f"比赛的主世界类型是{latest_match.seedType}，不在指定的范围内："
                  f"{config.clip_setting[latest_match.type_.name].seed_type}，跳过")
            return None
        if latest_match.category != "ANY":
            print(f"比赛的项目是{latest_match.category}，不是ANY%速通，跳过")
            return None
        if latest_match.id_ in self._cliped_matches:
            print(f"比赛已经被切片过，跳过")
            return None

        self._cliped_matches.append(latest_match.id_)
        return latest_match

    def get_user_data(self) -> UserData:
        api = f"{RankedService._RANKED_API}{self._name}"
        return UserData(**(requests.get(api).json()["data"]))

    def get_match_data(self, id_: int) -> MatchData:
        api = f"{RankedService._MATCH_API}{id_}"
        return MatchData(**(requests.get(api).json()["data"]))


ranked_service = RankedService(name=config.player.name, uuid=config.player.uuid)
if __name__ == "__main__":
    print(ranked_service.get_latest_match())
    print(ranked_service.get_user_data())
    print(ranked_service.get_match_data(1909310))