from pathlib import Path
import subprocess
import json
from dataclasses import dataclass
from ranked_service import MatchInfo
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
            raise EnvironmentError("未找到ffprobe，请确保已安装FFmpeg并将ffprobe添加到系统环境变量！"
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
        sseof_seconds = match_info.result.time // 1000 + 15
        output_file_path = config.video_dir / f"match[{match_info.id_}].mp4"
        cmd = [
            "ffmpeg",
            "-sseof", f"-{sseof_seconds}",
            "-i", video_path,
            "-c", "copy",
            "-avoid_negative_ts", "1",
            str(output_file_path)
        ]
        subprocess.run(cmd)
        print(f"已生成切片{output_file_path}")
        return output_file_path

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
    ffmpeg_service = FfmpegService()

