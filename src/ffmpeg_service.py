from pathlib import Path
import subprocess
import json
from dataclasses import dataclass
from ranked_service import MatchInfo, MatchType, MatchData
from config import config
import shutil

class FfmpegService:
    @dataclass
    class VideoInfo:
        width: int
        height: int
        size: float
        bit_rate: int
        frame_rate: float

    def __init__(self):
        try:
            self._check()
        except Exception as e:
            input(e.args[0])
            exit()

    @staticmethod
    def _check():
        if shutil.which("ffprobe") is None:
            raise EnvironmentError("未找到ffprobe，请确保已安装FFmpeg并将ffprobe添加到系统环境变量！"
                                   "（https://github.com/BtbN/FFmpeg-Builds/releases）")
        if shutil.which("ffmpeg") is None:
            raise EnvironmentError("未找到ffmpeg，请确保已安装FFmpeg并将ffmpeg添加到系统环境变量！"
                                   "（https://github.com/BtbN/FFmpeg-Builds/releases）")

        print("ffmpeg检查通过！")


    @staticmethod
    def get_video_info(file_path: Path) -> VideoInfo:
        command = [
            "ffprobe",
            "-v", "error",  # 只输出错误信息
            "-select_streams", "v:0",  # 只选择第一个视频流
            "-show_entries", "stream=width,height,r_frame_rate,bit_rate,duration",  # 选择需要的字段
            "-show_format",  # 获取文件格式信息
            "-print_format",
            "json",
            str(file_path)
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE)
        video_info = json.loads(result.stdout)
        # 提取相关信息
        stream = video_info.get("streams", [])[0]
        format_info = video_info.get("format", {})

        return FfmpegService.VideoInfo(
            width=stream.get("width"),
            height=stream.get("height"),
            size=float(format_info.get("size", 0)),
            bit_rate=int(format_info.get("bit_rate", 0)), # 单位 bps
            frame_rate=eval(stream.get("r_frame_rate", "0"))  # 转换帧率为浮点数
        )


    @staticmethod
    def auto_cut(match_info: MatchInfo, video_path: Path) -> Path:
        if match_info.type_ == MatchType.PRIVATE_ROOM_MATCH:
            print("警告：当前为私人房间，如果未设置'当有人完成时比赛结束'则可能剪辑不准确！")
        sseof_seconds = match_info.result.time // 1000 + config.extra_seconds
        output_file_path = config.video_dir / f"match[{match_info.id_}].{config.output_format}"
        cmd = [
            "ffmpeg",
            "-sseof", f"-{sseof_seconds}",
            "-i", video_path,
            "-c", "copy",
            "-avoid_negative_ts", "1",
            str(output_file_path)
        ]
        subprocess.run(cmd, capture_output=True)
        print(f"已生成切片{output_file_path}")
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

        ret: list[Path] = []

        for death_timeline in death_timeline_list:
            sseof_seconds = match_data.result.time // 1000 - death_timeline.time // 1000 + config.death_clip_duration + config.death_clip_ahead_seconds
            output_file_path = config.death_clip_dir / f"match[{match_data.id_}]{death_timeline.time}.{config.output_format}"
            cmd = [
                "ffmpeg",
                "-sseof", f"-{sseof_seconds}",
                "-t", str(config.death_clip_duration),
                "-i", video_path,
                "-c", "copy",
                "-avoid_negative_ts", "1",
                str(output_file_path)
            ]
            subprocess.run(cmd, capture_output=True)
            print(f"已生成死亡切片{output_file_path}")
            ret.append(output_file_path)
            file_list.append(f"file '{output_file_path.name}'\n")

        with open(config.death_clip_dir / "filelist.txt", "w") as _filelist:
            _filelist.writelines(file_list)
        return ret

    @staticmethod
    def screenshot(video_path: Path, ss: int, output_path: Path):
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss", str(ss),
                "-i", str(video_path),
                "-update", "1",
                "-q:v", "1",
                "-frames:v", "1",
                str(output_path),
            ]
            ,capture_output=True
        )



ffmpeg_service = FfmpegService()


if __name__ == "__main__":
    pass

