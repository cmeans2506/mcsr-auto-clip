from ranked_service import UserData, MatchData
from pathlib import Path
from config import config
from translator import translator
from datetime import datetime
import util
from ffmpeg_service import ffmpeg_service

class DescriptionGenerator:
    def __init__(self, match_data: MatchData, user_data: UserData, video_path: Path):
        self._match_data = match_data
        self._user_data = user_data
        self._video_path = video_path

        self._video_info = ffmpeg_service.get_video_info(self._video_path)

    def _generate_timelines_info(self):
        def timeline_to_str(timeline: MatchData.Timeline) -> str:
            if timeline.uuid != config.player.uuid or translator.timeline_map.get(timeline.type_) is None:
                return ""

            split = f"{util.ts_to_str(timeline.time)}    {translator.timeline_map[timeline.type_]}"
            opponent_timeline = self._match_data.get_opponent_timeline(timeline.type_)
            if opponent_timeline is None:
                return split

            time_delta = util.ts_to_str(abs(timeline.time - opponent_timeline.time))
            sign = "-" if timeline.time < opponent_timeline.time else "+"
            split += f"({sign}{time_delta})"
            return split

        timelines = self._match_data.timelines
        timelines_info_list = [
            timelines_info
            for timeline in reversed(timelines)
            if (timelines_info := timeline_to_str(timeline=timeline)) != ""
        ]
        return "\n".join(timelines_info_list)


    def _generate_match_info(self):
        players = self._match_data.players
        changes = self._match_data.changes
        match_info_str = f"""比赛模式: {translator.match_type_map[self._match_data.type_.name]}
        
{players[0].nickname} 大战 {players[1].nickname}

比赛结果: """
        for ch in changes:
            if ch.change is not None and ch.eloRate is not None:
                match_info_str += f"""
{self._match_data.get_player(ch.uuid).nickname:<16}{"胜" if ch.change > 0 else "败"}  ({ch.eloRate}  →  {ch.eloRate + ch.change})
"""
        match_info_str +=f"""
当前赛季: 第{self._match_data.season}赛季
比赛时间: {datetime.fromtimestamp(self._match_data.date).strftime("%Y-%m-%d %H:%M:%S")}
种子类型: {translator.seedtype_map[self._match_data.seedType]}
猪堡类型: {translator.bastion_map[self._match_data.bastionType]}"""
        return match_info_str


    def _generate_user_info(self):
        total_match_count = self._user_data.statistics.season.playedMatches.ranked
        if total_match_count == 0:
            return f"""MC名称：{self._user_data.nickname}
elo分：{self._user_data.eloRate}
elo排名：{self._user_data.eloRank}"""

        season_stats = self._user_data.statistics.season
        return f"""MC名称：{self._user_data.nickname}
elo分：{self._user_data.eloRate}
elo排名：{self._user_data.eloRank}
个人最佳：{util.ts_to_str(season_stats.bestTime.ranked)}
最高连胜：{season_stats.highestWinStreak.ranked}
总场次数：{total_match_count}
游玩时长：{int(season_stats.playtime.ranked / (1000 * 60 * 60))}小时
平均完成：{util.ts_to_str(season_stats.completionTime.ranked // season_stats.completions.ranked)}
投降场次：{season_stats.forfeits.ranked} ({round(100 * season_stats.forfeits.ranked / total_match_count, 2)}%)
完成场次：{season_stats.completions.ranked} ({round(100 * season_stats.completions.ranked / total_match_count, 2)}%)
胜利场次：{season_stats.wins.ranked} ({round(100 * season_stats.wins.ranked / total_match_count, 2)}%)
失败场次：{season_stats.loses.ranked} ({round(100 * season_stats.loses.ranked / total_match_count, 2)}%)
本赛季最高：{self._user_data.seasonResult.highest}
本赛季最低：{self._user_data.seasonResult.lowest}"""


    def _generate_upload_reason(self):
        minutes = config.upload_setting[self._match_data.type_.name].max_time // (60 * 1000)
        seconds = config.upload_setting[self._match_data.type_.name].max_time // 1000 % 60
        upload_reason = f"①sub{minutes}{seconds}"
        return upload_reason


    def _generate_about_info(self):
        return f""" · 本场速通详细信息：https://mcsrrankedstats.vercel.app/{config.player.name}/{self._match_data.id_}/
 · 更多详情：https://mcsrranked.com/api/matches/{self._match_data.id_}"""


    def _generate_video_info(self):
        return f"""宽度：{self._video_info.width}
高度：{self._video_info.height}
帧率：{self._video_info.frame_rate}
码率：{int(self._video_info.bit_rate / 1024)}kbps
文件大小：{int(self._video_info.size / (1024 * 1024))}MB"""

    def _generate_repository_info(self):
        return """MCSR AUTO CLIP by @-Cmeans- (https://b23.tv/VyvEo6u) 
开源地址：https://github.com/cmeans2506/mcsr-auto-clip
"""

    def generate_video_desc(self):
        return f"""{'大会员请开4K' if self._video_info.height > 1600 else ''}

■ 分段详情：
{self._generate_timelines_info()}

■ 比赛详情：
{self._generate_match_info()}

■ 个人信息（本赛季）：
{self._generate_user_info()}

■ 投稿条件：
{self._generate_upload_reason()}

■ 相关链接：
{self._generate_about_info()}

■ 视频信息：
{self._generate_video_info()}

■ 项目信息：
{self._generate_repository_info()}
"""
