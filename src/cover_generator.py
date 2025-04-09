from jinja2 import Template
import shutil
from config import config
from html2image import Html2Image
from ffmpeg_service import ffmpeg_service
from pathlib import Path
from ranked_service import MatchInfo, ranked_service
import util


class CoverGenerator:
    def __init__(self):
        with open("../templates/cover_for_ranked.html", "r", encoding="utf8") as template_file:
            self._template = Template(template_file.read())

        try:
            self._check()
        except Exception as e:
            input(e.args[0])
            exit()

        self._hti = Html2Image(output_path=str(config.video_dir), browser_executable=config.browser_executable)

    @staticmethod
    def _check():
        if shutil.which(config.browser_executable) is None:
            raise EnvironmentError("未找到chrome.exe，请确保已在config.json中配置正确！"
                                   "（https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Win_x64%2F1250504%2Fchrome-win.zip?generation=1705968802991678&alt=media）")

        print("CoverGenerator检查通过！")

    def generate(self, video_path: Path, match_info: MatchInfo) -> Path:
        bg_path = config.video_dir / f'BG match[{match_info.id_}].jpg'
        ranked_icon_path = config.template_dir / "image" / "ranked_icon.png"
        font_path = config.template_dir / "fonts" / "mc.ttf"
        ffmpeg_service.screenshot(video_path=video_path, ss=120, output_path=bg_path)
        html_content = self._template.render(
            font_path=font_path.as_posix(),
            bg_path=bg_path.as_posix(),
            left_player=match_info.get_my_info().model_dump(include={'nickname', 'uuid'}),
            right_player=match_info.get_opponent_info().model_dump(include={'nickname', 'uuid'}),
            ranked_icon=ranked_icon_path.as_posix(),
            match_id=match_info.id_,
            result_time=util.ts_to_str(match_info.result.time)
        )
        save_as = f'cover match[{match_info.id_}].jpg'
        ret = self._hti.screenshot(html_str=html_content, save_as=save_as)

        return Path(ret[0])


if __name__ == "__main__":
    cover_generator = CoverGenerator()
    cover_generator.generate(video_path=Path(r"D:\OBS VIdeos\2025-03-06 15-52-44.mp4"),
                             match_info=ranked_service.get_recent_matches()[0])