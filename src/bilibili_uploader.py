import shutil
from config import config
import subprocess
from pydantic import BaseModel, Field
import json
from pathlib import Path
from video_info_generator import VideoInfoGenerator
import re
from datetime import  datetime


class BilibiliUploader:
    class UploadHistoryInfo(BaseModel):
        id_: int = Field(alias='id')
        type_: str = Field(alias='type')
        aid: str
        bvid: str
        title: str
        upload_time: str

    def __init__(self):
        self._biliup_path: Path = config.base_dir / "biliup.exe"
        try:
            self._check()
        except Exception as e:
            input(e.args[0])
            exit()

        self._upload_history_list: list[BilibiliUploader.UploadHistoryInfo] = []
        self._up_history_path: Path = config.base_dir / "up_history.json"
        if self._up_history_path.exists():
            with open(self._up_history_path, "r", encoding="utf8") as up_history_file:
                self._upload_history_list = json.load(up_history_file)


    def _check(self):
        if shutil.which(self._biliup_path) is None:
            raise EnvironmentError(f"未找到biliup，请确保已将biliup.exe添加到{config.base_dir}")

        if not (config.base_dir / "cookies.json").exists():
            raise EnvironmentError(f"biliup未登录，请登录！(在'{config.base_dir}'下打开终端，输入'./biliup login')")

        print("BilibiliUploader检查通过！")

    @staticmethod
    def _parse_aid_bvid(log) -> (str, str):
        aid_pattern = r'"aid": Number\((\d+)\)'
        bvid_pattern = r'"bvid": String\("([^"]+)"\)'

        aid_match = re.search(aid_pattern, log)
        bvid_match = re.search(bvid_pattern, log)

        aid = aid_match.group(1) if aid_match else None
        bvid = bvid_match.group(1) if bvid_match else None
        return aid, bvid


    def _write_back(self):
        with open(self._up_history_path, "w", encoding="utf8") as up_history_file:
            history_data = [item.model_dump_json(by_alias=True) for item in self._upload_history_list]
            json.dump(history_data, up_history_file, indent=4)


    def upload(self, video_info: VideoInfoGenerator.VideoInfo):
        cmd = [
            str(self._biliup_path),
            "upload",
            "--copyright", "1",
            "--tid", "17",
            *(["--cover", str(video_info.cover_path)] if config.use_cover else []),
            "--title", video_info.video_title,
            "--desc", video_info.video_desc,
            "--tag", ",".join(video_info.video_tags),
            str(video_info.video_path),
        ]
        print(f"uploading: {video_info.video_title}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=config.base_dir)
        if result.returncode != 0:
            print("文件上传失败，请检查！")
            print("标准错误:", result.stderr)
            input()
            return
        aid, bvid = BilibiliUploader._parse_aid_bvid(result.stdout)
        print(f"<{video_info.video_title}>文件已经上传至{bvid}")

        self._upload_history_list.append(
            BilibiliUploader.UploadHistoryInfo(
                id=video_info.match_data.id_,
                type="RANKED",
                aid=aid,
                bvid=bvid,
                title=video_info.video_title,
                upload_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        self._write_back()

bilibili_uploader = BilibiliUploader()
if __name__ == "__main__":
    pass