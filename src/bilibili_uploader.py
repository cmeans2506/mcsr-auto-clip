import shutil
import subprocess
from pydantic import BaseModel, Field
import json
from pathlib import Path
import re
from datetime import  datetime
import threading
from tkinter import messagebox
from typing import Optional, Literal
from dataclasses import dataclass

import util
from config import config
from logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class UploadInfo:
    id: int
    type: Literal["RANKED", "RSG"]
    cover_path: Optional[Path]
    video_title: str
    video_desc: str
    video_tags: list[str]
    video_path: Path


class BiliUploader:
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
            logger.warning(e.args[0])
            input()
            exit()

        self._upload_history_list: list[BiliUploader.UploadHistoryInfo] = []
        self._up_history_path: Path = config.base_dir / "up_history.json"
        if self._up_history_path.exists():
            with open(self._up_history_path, "r", encoding="utf8") as up_history_file:
                self._upload_history_list = [BiliUploader.UploadHistoryInfo(**up_history) for up_history in json.load(up_history_file)]


    def _check(self):
        if shutil.which(self._biliup_path) is None:
            raise EnvironmentError(f"未找到biliup，请确保已将biliup.exe添加到{config.base_dir}")

        if not (config.base_dir / "cookies.json").exists():
            raise EnvironmentError(f"biliup未登录，请登录！(在'{config.base_dir}'下打开终端，输入'./biliup login')")

        logger.info("BilibiliUploader检查通过！")

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
        logger.info("上传历史已写入文件")


    def _upload_task(self, video_info: UploadInfo):
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
        logger.info(f"正在上传: {video_info.video_title}")
        logger.debug(f"正在运行: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", cwd=config.base_dir)
        except subprocess.CalledProcessError as e:
            if config.use_messagebox:
                messagebox.showerror("文件上传失败！", f"退出码: {e.returncode}\nstderr：{e.stderr}")
            logger.warning("文件上传失败！", f"退出码: {e.returncode}\nstderr：{e.stderr}")
            return
        aid, bvid = BiliUploader._parse_aid_bvid(result.stdout)
        if config.use_messagebox:
            messagebox.showinfo("文件上传成功！", f"{video_info.video_title} 已经上传至{bvid}")
        logger.info(f"{video_info.video_title} 已经上传至{bvid}")

        with self._lock:
            self._upload_history_list.append(
                BiliUploader.UploadHistoryInfo(
                    id=video_info.id,
                    type=video_info.type,
                    aid=aid,
                    bvid=bvid,
                    title=video_info.video_title,
                    upload_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            self._write_back()

    def upload(self, video_info: UploadInfo):
        thread = threading.Thread(
            target=self._upload_task,
            args=(video_info,),
            name=f"Upload-{video_info.video_title}",
            daemon=True
        )
        thread.start()

    def get_upload_history_by_id(self, id_: int) -> Optional[UploadHistoryInfo]:
        with self._lock:
            return util.find_first(lambda u: u.id_ == id_, self._upload_history_list)

bilibili_uploader = BiliUploader()
if __name__ == "__main__":
    pass