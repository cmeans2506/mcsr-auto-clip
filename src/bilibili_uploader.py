import shutil
from config import config
import subprocess
from pydantic import BaseModel, Field
import json
from pathlib import Path
from video_info_generator import VideoInfoGenerator
import re
from datetime import  datetime
import threading
from tkinter import messagebox


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
        self._lock = threading.Lock()
        try:
            self._check()
        except Exception as e:
            input(e.args[0])
            exit()

        self._upload_history_list: list[BilibiliUploader.UploadHistoryInfo] = []
        self._up_history_path: Path = config.base_dir / "up_history.json"
        if self._up_history_path.exists():
            with open(self._up_history_path, "r", encoding="utf8") as up_history_file:
                self._upload_history_list = [BilibiliUploader.UploadHistoryInfo(**up_history) for up_history in json.load(up_history_file)]


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
            history_data = [item.model_dump(by_alias=True) for item in self._upload_history_list]
            json.dump(history_data, up_history_file, indent=4)


    def _upload_task(self, video_info: VideoInfoGenerator.VideoInfo):
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
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", cwd=config.base_dir)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("文件上传失败！", f"退出码: {e.returncode}\nstderr：{e.stderr}")
            return
        aid, bvid = BilibiliUploader._parse_aid_bvid(result.stdout)
        messagebox.showinfo("文件上传成功！", f"<{video_info.video_title}>文件已经上传至{bvid}")
        print(f"<{video_info.video_title}>文件已经上传至{bvid}")

        with self._lock:
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

    def upload(self, video_info: VideoInfoGenerator.VideoInfo):
        thread = threading.Thread(
            target=self._upload_task,
            args=(video_info,),
            name=f"Upload-{video_info.video_title}",
            daemon=True
        )
        thread.start()

bilibili_uploader = BilibiliUploader()
if __name__ == "__main__":
    pass