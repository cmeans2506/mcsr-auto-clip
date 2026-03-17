from typing import Optional, Any
from pathlib import Path

from ranked.ranked_service import MatchInfo, RankedService
import util
from config import config
from base.base_cover_generator import BaseCoverGenerator
from logger import setup_logger

logger = setup_logger(__name__)

class CoverGenerator(BaseCoverGenerator):
    RANKED_ICON_PATH = config.template_dir / "image" / "ranked_icon.png"
    FONT_PATH = config.template_dir / "fonts" / "mc.ttf"
    def __init__(self, video_path: Path, match_info: MatchInfo):
        super().__init__(video_path=video_path)
        self.match_info = match_info

    def get_template_file_path(self) -> Path:
        return config.template_dir / "cover_for_ranked.html"

    def should_render_html(self) -> bool:
        if len(self.match_info.players) != 2:
            logger.info(f"Not a 1v1 match. Using {self.get_bg_path()} directly as the cover.")
            return False
        return True

    def get_bg_path(self) -> Path:
        return config.ranked_video_dir / f'bg[{self.match_info.id_}].webp'

    def get_render_data(self) -> dict[str, Any]:
        return {
            'font_path': self.get_base64(self.FONT_PATH),
            'bg_path': self.get_base64(self.get_bg_path()),
            'left_player': self.match_info.get_my_info().model_dump(include={'nickname', 'uuid'}),
            'right_player': self.match_info.get_opponent_info().model_dump(include={'nickname', 'uuid'}),
            'ranked_icon': self.get_base64(self.RANKED_ICON_PATH),
            'match_id': self.match_info.id_,
            'result_time': util.ts_to_str(self.match_info.result.time)
        }

    def get_save_path(self) -> Path:
        return config.ranked_video_dir / f'cover[{self.match_info.id_}].jpg'

    def get_html_path(self) -> Path:
        return config.ranked_video_dir / f'cover[{self.match_info.id_}].html'


def main():
    ranked_service = RankedService()
    cover_generator = CoverGenerator(
        video_path=Path(r"D:\视频\ranked\20251226\match[4342206].mp4"),
                         match_info=ranked_service.get_recent_matches()[0])
    cover_generator.generate()

if __name__ == "__main__":
    main()