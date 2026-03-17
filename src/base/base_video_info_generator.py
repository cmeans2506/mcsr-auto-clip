from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional

from bilibili_uploader import UploadInfo, VideoType

from logger import setup_logger

logger = setup_logger(__name__)


class BaseVideoInfoGenerator(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_video_title(self) -> str:
        pass

    @abstractmethod
    def get_title_file_path(self) -> Path:
        pass

    @abstractmethod
    def get_video_id(self) -> int:
        pass

    @abstractmethod
    def get_video_type(self) -> VideoType:
        pass

    @abstractmethod
    def generate_video_cover(self) -> Optional[Path]:
        pass

    @abstractmethod
    def generate_video_desc(self) -> str:
        pass

    @abstractmethod
    def generate_video_tags(self) -> list[str]:
        pass

    def generate_video_title(self) -> str:
        title = self.get_video_title()
        title_file_path = self.get_title_file_path()
        title_file_path.write_text(title, encoding="utf8")
        logger.debug(f"Title has been written to: {title_file_path}")
        return title

    @abstractmethod
    def get_video_path(self) -> Path:
        pass

    def generate(self) -> UploadInfo:
        return UploadInfo(
            id=self.get_video_id(),
            type=self.get_video_type(),
            cover_path=self.generate_video_cover(),
            video_title=self.generate_video_title(),
            video_desc=self.generate_video_desc(),
            video_tags=self.generate_video_tags(),
            video_path=self.get_video_path(),
        )

