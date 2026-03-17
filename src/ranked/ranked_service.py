from typing import Optional
from pydantic import BaseModel, Field
import requests
from datetime import datetime
from functools import cache
from cachetools import TTLCache, cached
from mcsr_enums import MatchType, SeedType, BastionType, TimelineType

from config import config
import util as util
from my_exceptions import PlayerNotFoundException, RankedAPIUnavailableError
from logger import setup_logger

logger = setup_logger(__name__)


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


# MatchInfo 是简化版的比赛信息，后面的 MatchData 是详细的
class MatchInfo(BaseModel):
    id_: int = Field(alias='id')
    type_: MatchType = Field(alias='type')
    category: Optional[str]
    players: list[Player]
    result: Result
    forfeited: bool
    decayed: bool
    changes: list[Change]
    season: int
    date: int
    seedType: Optional[SeedType]
    bastionType: Optional[BastionType]

    def get_opponent_info(self) -> Player:
        return next(filter(lambda player_info: player_info.uuid != config.player.uuid, self.players), None)
    def get_my_info(self) -> Player:
        return next(filter(lambda player_info: player_info.uuid == config.player.uuid, self.players), None)

    @property
    def is_valid_for_upload(self) -> bool:
        if self.result.time > config.upload_setting.ranked[self.type_.name].max_time:
            return False
        if self.bastionType not in config.upload_setting.ranked[self.type_.name].bastion_type:
            return False
        if self.seedType not in config.upload_setting.ranked[self.type_.name].seed_type:
            return False
        return True

    def __str__(self) -> str:
        my_info = self.get_my_info()
        if my_info and my_info.uuid == self.result.uuid:
            result = "win"
        else:
            result = "lose"

        if self.forfeited:
            time_part = "ff"
        elif result == "win":
            time_part = util.ts_to_str_sec(self.result.time)
        else:
            time_part = "N/A"

        current_time = datetime.now().timestamp()
        time_diff = current_time - self.date

        if time_diff < 3600:
            minutes_ago = int(time_diff / 60)
            time_diff_str = f"{minutes_ago} minutes ago"
        elif time_diff < 86400:
            hours_ago = int(time_diff / 3600)
            time_diff_str = f"{hours_ago} hours ago"
        else:
            days_ago = int(time_diff / 86400)
            time_diff_str = f"{days_ago} days ago"

        return f"{self.type_} - {result} - {time_part} - {self.seedType} - {time_diff_str}"


class RankedCasualStats(BaseModel):
    ranked: Optional[int] = None
    casual: Optional[int] = None

class StatisticsCategory(BaseModel):
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

class Statistics(BaseModel):
    season: StatisticsCategory
    total: StatisticsCategory

class SeasonResult(BaseModel):
    highest: Optional[int]
    lowest: Optional[int]

class UserData(BaseModel):
    uuid: str
    nickname: str
    eloRate: Optional[int]
    eloRank: Optional[int]
    statistics: Statistics
    country: Optional[str]
    seasonResult: SeasonResult


class MatchData(BaseModel):
    class Timeline(BaseModel):
        uuid: str
        time: int
        type_: TimelineType = Field(alias="type")

    id_: int = Field(alias='id')
    type_: MatchType = Field(alias="type")
    category: str
    players: list[Player]
    result: Result
    forfeited: bool
    decayed: bool
    changes: list[Change]
    completions: list[Result]
    timelines: list[Timeline]
    season: int
    date: int
    seedType: SeedType
    bastionType: BastionType

    def get_opponent_timeline(self, type_: str) -> Optional[Timeline]:
        return util.find_first(lambda timeline:timeline.type_ == type_
                                           and timeline.uuid != config.player.uuid, self.timelines)

    def get_player(self, uuid: str) -> Player:
        return util.find_first(lambda p:p.uuid == uuid, self.players)


class RankedService:
    _RANKED_API = "https://mcsrranked.com/api/users/"
    _MATCH_API = "https://mcsrranked.com/api/matches/"
    _MATCHES_API_EXTENSION = "/matches"

    _get_recent_matches_cache = TTLCache(maxsize=128, ttl=5)

    def __init__(self):
        """

        :param name: 玩家名称
        :param uuid: 玩家的uuid
        """

        self._any_clip_matches: list[int] = []
        self._death_clip_matches: list[int] = []
        self._session = requests.Session()

    @staticmethod
    @cache
    def get_uuid(name: str) -> str:
        """
        请求错误：requests.exceptions.RequestException
        玩家不存在：requests.exceptions.HTTPError
        :param name:
        :return: uuid
        """
        logger.info(f"Fetching UUID for player: {name}")
        api = f"{RankedService._RANKED_API}{name}"
        try:
            response = requests.get(api)

            if response.status_code == 400:
                logger.warning(f"Player '{name}' not found. Please check if the 'player' field is configured correctly.")
                raise PlayerNotFoundException(name)

            response.raise_for_status()
            return response.json()["data"]["uuid"]
        except requests.exceptions.RequestException as e:
            if e.response.status_code == 429:
                logger.warning("Ranked API rate limit exceeded. Please try again later.")
            else:
                logger.warning(f"Error during request to {e.request.url}. Please check your network connection.")
            raise RankedAPIUnavailableError(api, e) from e

    @staticmethod
    @cache
    def get_uuid_mojang(name: str) -> str:
        logger.info(f"Fetching UUID for {name} from Mojang API")
        api = f"https://api.mojang.com/users/profiles/minecraft/{name}"

        try:
            response = requests.get(api, timeout=10)
            if response.status_code == 204:
                logger.warning(f"Mojang API could not find player '{name}'")
                raise PlayerNotFoundException(name)
            response.raise_for_status()
            data = response.json()
            return data["id"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("Mojang API rate limit exceeded. Please try again later.")
            elif e.response.status_code == 404:
                raise PlayerNotFoundException(name)
            raise
        except Exception as e:
            logger.error(f"Error accessing Mojang API: {e}")
            raise

    @cached(_get_recent_matches_cache)
    def get_recent_matches(self, match_type: Optional[MatchType] = None, count: int = 50) -> list[MatchInfo]:
        api = f"{RankedService._RANKED_API}{config.player.name}{RankedService._MATCHES_API_EXTENSION}?count={count}"
        if match_type is not None:
            api += f"&type={match_type.value}"
        try:
            response = self._session.get(api)

            if response.status_code == 400:
                logger.warning(f"Player '{config.player.name}' not found. Please check if the 'player' field is configured correctly.")
                raise PlayerNotFoundException(config.player.name)

            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            if e.response.status_code == 429:
                logger.warning("Ranked API rate limit exceeded. Please try again later.")
            else:
                logger.warning(f"Error during request to {e.request.url}. Please check your network connection.")
            return []

        return [MatchInfo(**match_info) for match_info in data["data"]]

    def get_latest_match(self) -> Optional[MatchInfo]:
        if not config.ranked_job:
            return None

        match_info_list = self.get_recent_matches(count=5)
        if not match_info_list:
            logger.info(f"No recent matches found for: {config.player.name}")
            return None

        latest_match = match_info_list[0]
        logger.info(f"Latest match found: {latest_match}")

        if latest_match.date < config.launch_time:
            logger.info("Match ended before script launch. Skipping.")
            return None
        if latest_match.result.uuid != config.player.uuid:
            logger.info("Match was not a victory. Skipping.")
            return None
        if latest_match.forfeited or latest_match.decayed:
            logger.info("Incomplete match (forfeited or decayed). Skipping.")
            return None
        if latest_match.result.time > config.clip_setting.ranked[latest_match.type_.name].max_time:
            logger.info(f"Completion time {util.ts_to_str(latest_match.result.time)} exceeds the maximum allowed "
                        f"{util.ts_to_str(config.clip_setting.ranked[latest_match.type_.name].max_time)}. Skipping.")
            return None
        if latest_match.bastionType not in config.clip_setting.ranked[latest_match.type_.name].bastion_type:
            logger.info(f"Bastion type '{latest_match.bastionType}' is not in the allowed list: "
                        f"{config.clip_setting.ranked[latest_match.type_.name].bastion_type}. Skipping.")
            return None
        if latest_match.seedType not in config.clip_setting.ranked[latest_match.type_.name].seed_type:
            logger.info(f"Overworld seed type '{latest_match.seedType}' is not in the allowed list: "
                        f"{config.clip_setting.ranked[latest_match.type_.name].seed_type}. Skipping.")
            return None
        if latest_match.category != "ANY":
            logger.info(f"Match category is {latest_match.category}, not ANY%. Skipping.")
            return None
        if latest_match.id_ in self._any_clip_matches:
            logger.info("Match has already been clipped. Skipping.")
            return None

        self._any_clip_matches.append(latest_match.id_)
        return latest_match

    def get_latest_death_match(self) -> Optional[MatchData]:
        if not config.use_death_clip:
            return None

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

        logger.info(f"New death clip match detected: match[{latest_match_data.id_}]")
        self._death_clip_matches.append(latest_match_data.id_)
        return latest_match_data


    def get_user_data(self) -> UserData:
        api = f"{RankedService._RANKED_API}{config.player.name}"
        return UserData(**(self._session.get(api).json()["data"]))

    @cache
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