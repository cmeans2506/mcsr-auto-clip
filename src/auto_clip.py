import logging
import time
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from apscheduler.events import EVENT_JOB_ERROR

from ffmpeg_service import ffmpeg_service
from config import config
from bilibili_uploader import BiliUploader
from obs_controller import OBSController
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING, STATE_PAUSED

from gui.status_notifier import status_notifier
from ranked.video_info_generator import VideoInfoGenerator as RankedVideoInfoGenerator
from ranked.ranked_service import RankedService, MatchInfo
from rsg.video_info_generator import VideoInfoGenerator as RsgVideoInfoGenerator
from rsg.paceman_service import PacemanService
from rsg.rsg_pb import RsgPb
from logger import setup_logger

logger = setup_logger(__name__)
setup_logger('apscheduler', logging.WARNING)


class SchedulerErrorNotifier(QObject):
    signal = pyqtSignal(str)
scheduler_error_notifier = SchedulerErrorNotifier()

class AutoClip:
    def listener(self, event):
        if event.exception:
            scheduler_error_notifier.signal.emit(f"Job {event.job_id} failed to execute!\n\nException: {event.exception}\n\n"
                                                 f"Traceback:\n{event.traceback}")

    def on_obs_disconnect(self, obsws):
        if self.is_running:
            logger.warning("OBS disconnected. Stopping job execution!")
            self.background_scheduler.pause()

    def __init__(self):
        self.background_scheduler = BackgroundScheduler()
        self.background_scheduler.add_listener(self.listener, EVENT_JOB_ERROR)

        # 全局变量：一定创建实例，创建实例和检查环境逻辑分离，根据config中的配置决定是否启用
        # 局部变量：不一定创建实例，根据config中的配置决定是否创建实例，创建实例和检查环境逻辑不分离，根据实例是否为None决定是否启用
        self.obs_controller = OBSController(config.host, config.port, on_disconnect=self.on_obs_disconnect)
        self.ranked_service = RankedService()
        self.paceman_service = PacemanService()
        self.bili_uploader = BiliUploader()
        self.rsg_pb = RsgPb()

        self.background_scheduler.add_job(self._ranked_job, 'interval', seconds=10, id=self._ranked_job.__name__)
        self.background_scheduler.add_job(self._rsg_job, 'interval', seconds=10, id=self._rsg_job.__name__)


    def _rsg_job(self):
        live_run = self.paceman_service.get_latest_run()
        if live_run is None:
            return

        if live_run.is_complete_run:
            logger.info(f"Complete RSG run detected. Waiting {config.wait_for_datapack} seconds for /datapack list and /seed commands...")
            status_notifier.message_signal.emit(f"Waiting {config.wait_for_datapack} seconds for /datapack list and /seed commands...", config.wait_for_datapack * 1000)
            time.sleep(config.wait_for_datapack)

        raw_video_path = self.obs_controller.save_replay()
        logger.info(f"Saved replay for world [{live_run.id}]: {raw_video_path}")

        cut_video_path = ffmpeg_service.rsg_cut(live_run=live_run, video_path=raw_video_path)

        video_info_generator = RsgVideoInfoGenerator(live_run=live_run, video_path=cut_video_path, rsg_pb=self.rsg_pb)
        upload_info = video_info_generator.generate()

        # 接下来是上传的逻辑
        if not live_run.is_valid_for_upload and config.use_upload:
            self.bili_uploader.upload(upload_info)

        if config.use_rsg_pb:
            self.rsg_pb.check_for_pb(bili_uploader=self.bili_uploader, live_run=live_run)

        if config.clean_raw_file:
            raw_video_path.unlink()
            logger.info(f"Raw video file deleted: {raw_video_path}")


    def _ranked_job(self):
        latest_match = self.ranked_service.get_latest_match()
        latest_match_data = self.ranked_service.get_latest_death_match()

        if latest_match is None and latest_match_data is None:
            return

        raw_video_path = self.obs_controller.save_replay()
        logger.info(f"Saved replay for match [{latest_match.id_}]: {raw_video_path}")

        if latest_match is not None:
            self.ranked_any(match_info=latest_match, raw_video_path=raw_video_path)

        if latest_match_data is not None:
            cut_video_list = ffmpeg_service.death_clip(match_data=latest_match_data, video_path=raw_video_path)

            # 不上传

        if config.clean_raw_file:
            raw_video_path.unlink()
            logger.info(f"Raw video file deleted: {raw_video_path}")

    def ranked_any(self, match_info: MatchInfo, raw_video_path: Path):
        cut_video_path = ffmpeg_service.auto_cut(match_info=match_info, video_path=raw_video_path)
        match_data = self.ranked_service.get_match_data(match_info.id_)
        user_data = self.ranked_service.get_user_data()
        video_info_generator = RankedVideoInfoGenerator(
            match_data=match_data,
            match_info=match_info,
            user_data=user_data,
            video_path=cut_video_path
        )
        upload_info = video_info_generator.generate()
        if not match_info.is_valid_for_upload:
            return
        if config.use_upload:
            self.bili_uploader.upload(upload_info)


    def run(self):
        self.background_scheduler.start()

    def _safe_pause_job(self, job_id):
        job = self.background_scheduler.get_job(job_id)
        if job and job.next_run_time is not None:
            job.pause()

    def _safe_resume_job(self, job_id):
        job = self.background_scheduler.get_job(job_id)
        if job and job.next_run_time is None:
            job.resume()


    def start(self):
        if self.obs_controller is None:
            self.obs_controller = OBSController(config.host, config.port, on_disconnect=self.on_obs_disconnect)
        self.obs_controller.start()
        if config.ranked_job or config.use_death_clip:
            config.player.uuid = RankedService.get_uuid(config.player.name)
        else:
            config.player.uuid = RankedService.get_uuid_mojang(config.player.name)
        if config.use_upload:
            self.bili_uploader.check()
        ffmpeg_service.check()
        config.launch_time = time.time()

        if self.background_scheduler.state == STATE_PAUSED:
            self.background_scheduler.resume()
        elif self.background_scheduler.state != STATE_RUNNING:
            self.background_scheduler.start()


    def stop(self):
        if self.is_running:
            self.background_scheduler.pause()

        self.obs_controller.stop()

    @property
    def is_running(self):
        # BackgroundScheduler 官方有一个 running 的 property ，判断条件是 state 不为 STOPPED
        # 而 STOPPED 只有在 未启动、shutdown、调度器内部异常 的时候才会出现
        # 不适合本项目的场景，不使用
        return self.background_scheduler.state == STATE_RUNNING

auto_clip = AutoClip()
