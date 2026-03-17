import os
from pathlib import Path
import subprocess
import json
from dataclasses import dataclass
from rsg.paceman_service import LiveRunData
from config import config
import shutil

from gui.status_notifier import status_notifier
from ranked.ranked_service import MatchInfo, MatchType, MatchData
from my_exceptions import FfmpegNotConfiguredException
from logger import setup_logger

logger = setup_logger(__name__)

class FfmpegService:
    FFMPEG_PATH = config.assets_dir / "ffmpeg" / "bin" / "ffmpeg.exe"
    FFPROBE_PATH = config.assets_dir / "ffmpeg" / "bin" / "ffprobe.exe"

    @dataclass
    class VideoInfo:
        width: int
        height: int
        size: int       # MB
        bit_rate: int   # kbps
        frame_rate: int
        codec_name: str


    @staticmethod
    def check():
        if shutil.which(FfmpegService.FFPROBE_PATH) is None or shutil.which(FfmpegService.FFMPEG_PATH) is None:
            raise FfmpegNotConfiguredException()

        logger.info("ffmpeg check passed!")


    @staticmethod
    def get_video_info(file_path: Path) -> VideoInfo:
        logger.debug(f"Retrieving info for video: {file_path}")
        command = [
            str(FfmpegService.FFPROBE_PATH),
            "-v", "error",  # 只输出错误信息
            "-select_streams", "v:0",  # 只选择第一个视频流
            "-show_entries", "stream=width,height,r_frame_rate,bit_rate,duration,codec_name",  # 选择需要的字段
            "-show_format",  # 获取文件格式信息
            "-print_format", "json",
            str(file_path)
        ]
        logger.debug(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, stdout=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        logger.debug(f"ffprobe stdout: {result.stdout}")
        video_info = json.loads(result.stdout)
        # 提取相关信息
        stream = video_info["streams"][0]
        format_info = video_info["format"]

        # 在网络传输和多媒体领域，标准做法是使用 10 进制
        # 而在存储和内存领域，标准做法是使用 2 进制
        return FfmpegService.VideoInfo(
            width=stream["width"],
            height=stream["height"],
            size=int(os.path.getsize(file_path) / (1024 * 1024)),
            bit_rate=int(format_info["bit_rate"]) // 1000,
            frame_rate=int(eval(stream["r_frame_rate"])),
            codec_name=stream["codec_name"]
        )


    @staticmethod
    def auto_cut(match_info: MatchInfo, video_path: Path) -> Path:
        if match_info.type_ == MatchType.PRIVATE_ROOM_MATCH:
            logger.warning("Private room match detected. Clips might be inaccurate if 'Match ends with completions' is not set to 0!")
        sseof_seconds = match_info.result.time // 1000 + config.extra_seconds_ranked
        input_extension = Path(video_path).suffix
        output_file_path = config.ranked_video_dir / f"match[{match_info.id_}]{input_extension}"
        cmd = [
            str(FfmpegService.FFMPEG_PATH), "-y",
            "-sseof", f"-{sseof_seconds}",
            "-i", str(video_path),
            "-map", "0",
            "-c", "copy",
            "-avoid_negative_ts", "1",
            str(output_file_path)
        ]
        logger.debug(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        logger.debug(f"ffmpeg stdout: {result.stdout}")
        logger.info(f"Generated clip: {output_file_path}")
        status_notifier.message_signal.emit(f"Generated clip: {output_file_path}", 3000)
        return output_file_path


    @staticmethod
    def death_clip(match_data: MatchData, video_path: Path) -> list[Path]:
        def is_death_timeline(timeline: MatchData.Timeline) -> bool:
            return timeline.type_ == "projectelo.timeline.death" and timeline.uuid == config.player.uuid

        file_list = []
        if (config.death_clip_dir / "filelist.txt").exists():
            with open(config.death_clip_dir / "filelist.txt", "r") as _filelist:
                file_list = _filelist.readlines()

        death_timeline_list = filter(is_death_timeline, match_data.timelines)
        input_extension = Path(video_path).suffix

        ret: list[Path] = []

        for death_timeline in death_timeline_list:
            sseof_seconds = match_data.result.time // 1000 - death_timeline.time // 1000 + config.death_clip_duration + config.death_clip_ahead_seconds
            output_file_path = config.death_clip_dir / f"match[{match_data.id_}]{death_timeline.time}{input_extension}"
            cmd = [
                str(FfmpegService.FFMPEG_PATH), "-y",
                "-sseof", f"-{sseof_seconds}",
                "-t", str(config.death_clip_duration),
                "-i", str(video_path),
                "-map", "0",
                "-c", "copy",
                "-avoid_negative_ts", "1",
                str(output_file_path)
            ]
            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            logger.debug(f"ffmpeg stdout: {result.stdout}")
            logger.info(f"Generated death clip: {output_file_path}")
            ret.append(output_file_path)
            file_list.append(f"file '{output_file_path.name}'\n")

        with open(config.death_clip_dir / "filelist.txt", "w") as _filelist:
            _filelist.writelines(file_list)
        return ret

    @staticmethod
    def screenshot(video_path: Path, ss: int, output_path: Path):
        cmd = [
                str(FfmpegService.FFMPEG_PATH), "-y",
                "-ss", str(ss),
                "-discard", "nokey", # 丢弃非关键帧，无需精确定位到 ss 的位置，提速 (0.26s -> 0.09s)
                "-i", str(video_path),
                "-update", "1",
                "-q:v", "1",
                "-frames:v", "1",
                str(output_path),
        ]
        logger.debug(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        logger.debug(f"ffmpeg stdout: {result.stdout}")
        logger.info(f"Generated screenshot: {str(output_path)}")

    @staticmethod
    def rsg_cut(live_run: LiveRunData, video_path: Path) -> Path:
        sseof_seconds = live_run.rta + config.extra_seconds_rsg
        input_extension = Path(video_path).suffix
        output_file_path = config.rsg_video_dir / f"world[{live_run.id}]{input_extension}"
        cmd = [
            str(FfmpegService.FFMPEG_PATH),  "-y",
            "-sseof", f"-{sseof_seconds}",
            "-i", str(video_path),
            "-map", "0",
            "-c", "copy",
            "-avoid_negative_ts", "1",
            str(output_file_path)
        ]
        logger.debug(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        logger.debug(f"ffmpeg stdout: {result.stdout}")
        logger.info(f"Generated RSG clip: {output_file_path}")
        status_notifier.message_signal.emit(f"Generated RSG clip: {output_file_path}", 3000)
        return output_file_path



ffmpeg_service = FfmpegService()


if __name__ == "__main__":
    pass

