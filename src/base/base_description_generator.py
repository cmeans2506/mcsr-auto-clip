from abc import ABC, abstractmethod
from pathlib import Path
import inspect
from string import Template
from ffmpeg_service import ffmpeg_service
from dataclasses import asdict
from config import VERSION
from PyQt6.QtCore import QCoreApplication
from logger import setup_logger

logger = setup_logger(__name__)


class BaseDescriptionGenerator(ABC):
    def __init__(self, video_path: Path):
        self.video_path = video_path

        self.base_desc_template = Template(inspect.cleandoc(
            QCoreApplication.translate("BaseDescriptionGenerator", """
            $sub_template
            
            ■ Upload Conditions
            $upload_reason
                        
            ■ Links
            $about_info
                        
            ■ Video Info
            $video_info
                        
            ■ Repository Info
            $repository_info
                     
        """)
        ))

    @abstractmethod
    def generate_upload_reason(self) -> str:
        pass

    @abstractmethod
    def generate_about_info(self) -> str:
        pass

    # 2560x1440 @60fps 2.83mbps 319MB AV1
    def generate_video_info(self) -> str:
        video_info = ffmpeg_service.get_video_info(self.video_path)
        tmpl = Template("${width}x${height} @${frame_rate}fps ${bit_rate}kbps ${size}MB $codec_name")
        return tmpl.safe_substitute(asdict(video_info))

    def generate_repository_info(self):
        return Template(inspect.cleandoc("""
        
            MCSR AUTO CLIP $version by Cmeans
            https://github.com/cmeans2506/mcsr-auto-clip
            
        """)).safe_substitute(version=VERSION)

    @abstractmethod
    def generate_sub_template(self) -> str:
        pass

    @abstractmethod
    def get_desc_path(self) -> Path:
        pass

    def generate(self) -> str:
        desc = self.base_desc_template.safe_substitute(
            sub_template=self.generate_sub_template(),
            upload_reason=self.generate_upload_reason(),
            about_info=self.generate_about_info(),
            video_info=self.generate_video_info(),
            repository_info=self.generate_repository_info()
        )
        desc_path = self.get_desc_path()
        desc_path.write_text(desc)
        logger.debug(f"Description has been written to: {desc_path}")
        return desc

