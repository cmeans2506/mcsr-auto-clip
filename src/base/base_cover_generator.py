import base64
from abc import ABC, abstractmethod
from functools import cache
from typing import Optional

from playwright.sync_api import sync_playwright, ViewportSize
from jinja2 import Template
from pathlib import Path
import mimetypes

mimetypes.add_type("font/ttf", ".ttf")
mimetypes.add_type("font/otf", ".otf")
mimetypes.add_type("font/woff", ".woff")
mimetypes.add_type("font/woff2", ".woff2")

from ffmpeg_service import ffmpeg_service
from logger import setup_logger

logger = setup_logger(__name__)


class BaseCoverGenerator(ABC):
    def __init__(self, video_path: Path):
        self.video_path = video_path


    @staticmethod
    @cache
    def get_base64(resource_path: Path):
       mime_type, _ = mimetypes.guess_type(resource_path)
       if not mime_type:
           mime_type = "application/octet-stream"

       try:
           with open(resource_path, "rb") as resource_file:
               encoded = base64.b64encode(resource_file.read()).decode("utf-8")
               return f"data:{mime_type};base64,{encoded}"
       except Exception as e:
           logger.warning(f"无法读取{resource_path}, 错误: {e}")
           return ""


    @staticmethod
    def capture_screenshot(html_content: str, output_path: Path) -> Optional[Path]:
        """
        根据 html 字符串生成图片
        :param html_content: html 字符串
        :param output_path: 图片
        :return: 生成成功的时候返回生成图片的路径，生成错误的时候返回 None
        """
        with sync_playwright() as p:
            browser = None
            channels = ["chrome", "msedge"]

            for channel in channels:
                try:
                    logger.debug(f"正在尝试使用 {channel} 启动浏览器...")
                    browser = p.chromium.launch(channel=channel)
                    break
                except Exception as e:
                    logger.info(f"无法使用 {channel} 启动: {e}")

            if not browser:
                logger.warning("错误：无法启动 Chrome 或 Edge 浏览器。")
                return None

            try:
                v_size: ViewportSize = {"width": 1920, "height": 1080}

                context = browser.new_context(viewport=v_size)
                page = context.new_page()

                page.set_content(html_content, wait_until="networkidle")

                image_load_errors = page.evaluate("""
                () => {
                    const imgs = Array.from(document.images);
                    return imgs
                        .filter(img => !img.complete || img.naturalWidth === 0)
                        .map(img => img.src);
                }
                """)

                if image_load_errors:
                    logger.warning(f"图片未成功渲染：{image_load_errors}")
                    return None

                page.screenshot(path=output_path)
                logger.info(f"封面已生成至：{output_path}")
                return output_path

            except Exception as e:
                logger.warning(f"封面生成过程中发生错误：{e}")
                return None
            finally:
                browser.close()

    @abstractmethod
    def get_template_file_path(self) -> Path:
        pass

    def should_render_html(self) -> bool:
        return True

    @abstractmethod
    def get_bg_path(self) -> Path:
        pass

    @abstractmethod
    def get_render_data(self) -> dict[str, str]:
        pass

    @abstractmethod
    def get_save_path(self) -> Path:
        pass

    @abstractmethod
    def get_html_path(self) -> Path:
        pass


    def generate(self) -> Path:
        template = Template(self.get_template_file_path().read_text(encoding='utf8'))

        bg_path = self.get_bg_path()
        ffmpeg_service.screenshot(video_path=self.video_path, ss=120, output_path=bg_path)

        if not self.should_render_html():
            return bg_path

        html_content = template.render(**self.get_render_data())

        html_path = self.get_html_path()
        html_path.write_text(html_content, encoding="utf-8")
        logger.debug(f"封面html文件已写入 {html_path}")

        ret = self.capture_screenshot(html_content, self.get_save_path())
        if ret is None:
            logger.warning(f"封面生成时出错，直接使用 {bg_path} 作为封面")
            return bg_path

        return ret