import inspect
from pathlib import Path
from datetime import datetime
from string import Template

from config import config
from translator import translator
import util
from ranked.ranked_service import UserData, MatchData, RankedService
from base.base_description_generator import BaseDescriptionGenerator
from logger import setup_logger

logger = setup_logger(__name__)

class DescriptionGenerator(BaseDescriptionGenerator):
    def __init__(self, match_data: MatchData, user_data: UserData, video_path: Path):
        super().__init__(video_path=video_path)
        self._match_data = match_data
        self._user_data = user_data

        self.sub_template = Template(inspect.cleandoc("""        

            ■ 分段详情
            $timelines_info
            
            ■ 比赛详情
            $match_info
            
            ■ 个人信息
            $user_info
        
        """))


    def _generate_timelines_info(self):
        def timeline_to_str(timeline: MatchData.Timeline) -> str:
            event_label = translator.timeline_map.get(timeline.type_)
            if timeline.uuid != config.player.uuid or not event_label:
                return ""

            time_str = util.ts_to_str_sec(timeline.time)
            opp_tl = self._match_data.get_opponent_timeline(timeline.type_)

            delta_str = ""
            if opp_tl:
                sign = "-" if timeline.time < opp_tl.time else "+"
                diff_val = util.ts_to_str_sec(abs(timeline.time - opp_tl.time))
                delta_str = f"({sign}{diff_val})"

            return f"{time_str} {event_label} {delta_str}"

        timelines = self._match_data.timelines
        timelines_info_list = [
            timelines_info
            for timeline in reversed(timelines)
            if (timelines_info := timeline_to_str(timeline=timeline)) != ""
        ]
        return " || ".join(timelines_info_list)

    # Cmeans VS alkasm
    # 排位模式 / S9 / 2026-01-01 22:54:07 / 沉船 / 居住区
    def _generate_match_info(self):
        players = self._match_data.players

        tmpl = inspect.cleandoc("""
        
        {players_line}
        {match_type} / S{season} / {date} / {seedtype} / {bastion}
        
        """)

        return tmpl.format(
            players_line=" VS ".join([p.nickname for p in players]),
            match_type=translator.match_type_map[self._match_data.type_.name],
            season=self._match_data.season,
            date=datetime.fromtimestamp(self._match_data.date).strftime("%Y-%m-%d %H:%M:%S"),
            seedtype=translator.seedtype_map[self._match_data.seedType],
            bastion=translator.bastion_map[self._match_data.bastionType]
        )

    # Cmeans 1279(1573 peak) #1548 pb: 08:57 avg: 13:19 184h 胜：42% 投：13%
    def _generate_user_info(self):
        total_match_count = self._user_data.statistics.season.playedMatches.ranked
        season_stats = self._user_data.statistics.season

        avg = win_rate = ff_rate = 'N/A'
        if total_match_count != 0:
            avg = util.ts_to_str_sec(season_stats.completionTime.ranked // season_stats.completions.ranked)
            win_rate = round(100 * season_stats.wins.ranked / total_match_count, 1)
            ff_rate = round(100 * season_stats.forfeits.ranked / total_match_count, 1)

        tmpl = ("{nickname} {eloRate} #{eloRank} {highest}peak {playtime}h "
                "pb: {pb} avg: {avg} 胜: {win_rate}% 投: {ff_rate}% 总: {total_match_count}")

        return tmpl.format(
            nickname=self._user_data.nickname,
            eloRate=self._user_data.eloRate,
            highest=self._user_data.seasonResult.highest,
            eloRank=self._user_data.eloRank,
            pb=util.ts_to_str_sec(season_stats.bestTime.ranked),
            avg=avg,
            playtime=round(season_stats.playtime.ranked / (1000 * 60 * 60), 1),
            win_rate=win_rate,
            ff_rate=ff_rate,
            total_match_count=total_match_count
        )

    def generate_upload_reason(self):
        max_time = util.ts_to_str_sec(config.upload_setting.ranked[self._match_data.type_.name].max_time)
        upload_reason = f"①sub {max_time}"
        return upload_reason


    def generate_about_info(self):
        return inspect.cleandoc(f"""
        
             · 可视化：https://mcsrrankedstats.vercel.app/{config.player.name}/{self._match_data.id_}/
             · api：https://mcsrranked.com/api/matches/{self._match_data.id_}
             
        """)

    def generate_sub_template(self) -> str:
        return self.sub_template.safe_substitute(
            timelines_info=self._generate_timelines_info(),
            match_info=self._generate_match_info(),
            user_info=self._generate_user_info()
        )

    def get_desc_path(self) -> Path:
        return config.ranked_video_dir / f'desc[{self._match_data.id_}].txt'


def main():
    ranked_service = RankedService()
    desc_generator = DescriptionGenerator(
        video_path=Path(r"D:\OBS Videos\2025-06-27 19-24-48.mp4"),
        match_data=ranked_service.get_match_data(5330969),
        user_data=ranked_service.get_user_data()
    )
    print(desc_generator.generate())

if __name__ == "__main__":
    main()