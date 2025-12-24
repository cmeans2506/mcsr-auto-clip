import logging
import time

from PyQt6.QtCore import QObject, pyqtSignal
from apscheduler.events import EVENT_JOB_ERROR

from ffmpeg_service import ffmpeg_service
from config import config
from bilibili_uploader import BiliUploader
from obs_controller import OBSController
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING, STATE_PAUSED

from ranked.video_info_generator import VideoInfoGenerator as RankedVideoInfoGenerator
from ranked.ranked_service import RankedService
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
            scheduler_error_notifier.signal.emit(f"任务 {event.job_id} 执行出错！\n\n异常信息: {event.exception}\n\n"
                                                 f"Traceback:\n{event.traceback}")

    def on_obs_disconnect(self, obsws):
        if self.is_running:
            logger.warning("OBS断连，停止任务的执行！")
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
        self.background_scheduler.add_job(self.obs_controller.clean, 'interval', minutes=2, id=self.obs_controller.clean.__name__)
        self.background_scheduler.add_job(self._death_clip_job, 'interval', seconds=10, id=self._death_clip_job.__name__)


    def _ranked_job(self):
        latest_match = self.ranked_service.get_latest_match()
        if latest_match is None:
            return

        raw_video_path = self.obs_controller.save_replay()
        logger.info(f"存储了比赛[{latest_match.id_}]的录像：{raw_video_path}")

        cut_video_path = ffmpeg_service.auto_cut(match_info=latest_match, video_path=raw_video_path)

        # 接下来是上传的逻辑
        if not latest_match.is_valid_for_upload():
            return

        match_data = self.ranked_service.get_match_data(latest_match.id_)
        user_data = self.ranked_service.get_user_data()

        video_info_generator = RankedVideoInfoGenerator(
            match_data=match_data,
            match_info=latest_match,
            user_data=user_data,
            video_path=cut_video_path
        )
        if config.use_upload:
            self.bili_uploader.upload(video_info_generator.generate())

    def _rsg_job(self):
        live_run = self.paceman_service.get_latest_run()
        if live_run is None:
            return

        if live_run.is_complete_run():
            logger.info(f"本场rsg速通是完整速通，等待{config.wait_for_datapack}秒用于输入/datapack list和/seed等指令...")
            time.sleep(config.wait_for_datapack)

        world_data = self.paceman_service.get_world(live_run.worldId)

        raw_video_path = self.obs_controller.save_replay()
        logger.info(f"存储了世界[{world_data.data.id}]的录像：{raw_video_path}")

        cut_video_path = ffmpeg_service.rsg_cut(live_run=live_run, world_data=world_data, video_path=raw_video_path)

        # 接下来是上传的逻辑
        if not live_run.is_valid_for_upload():
            return

        video_info_generator = RsgVideoInfoGenerator(
            live_run=live_run, world_data=world_data, video_path=cut_video_path, rsg_pb=self.rsg_pb
        )
        if config.use_upload:
            self.bili_uploader.upload(video_info_generator.generate())
        if config.use_rsg_pb:
            self.rsg_pb.check_for_pb(bili_uploader=self.bili_uploader, live_run=live_run, world_data=world_data)


    def _death_clip_job(self):
        latest_match_data = self.ranked_service.get_latest_death_match()
        if latest_match_data is None:
            return

        raw_video_path = self.obs_controller.save_replay()
        logger.info(f"存储了比赛[{latest_match_data.id_}]的录像：{raw_video_path}")

        cut_video_list = ffmpeg_service.death_clip(match_data=latest_match_data, video_path=raw_video_path)

        # 不上传

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
        config.player.uuid = RankedService.get_uuid(config.player.name)
        if config.use_upload:
            self.bili_uploader.check()
        ffmpeg_service.check()
        config.launch_time = time.time()

        if self.background_scheduler.state == STATE_PAUSED:
            self.background_scheduler.resume()
        elif self.background_scheduler.state != STATE_RUNNING:
            self.background_scheduler.start()

        if config.ranked_job:
            self._safe_resume_job(self._ranked_job.__name__)
        else:
            self._safe_pause_job(self._ranked_job.__name__)

        if config.rsg_job:
            self._safe_resume_job(self._rsg_job.__name__)
        else:
            self._safe_pause_job(self._rsg_job.__name__)

        if config.use_death_clip:
            self._safe_resume_job(self._death_clip_job.__name__)
        else:
            self._safe_pause_job(self._death_clip_job.__name__)

        if config.clean_raw_file:
            self._safe_resume_job(self.obs_controller.clean.__name__)
        else:
            self._safe_pause_job(self.obs_controller.clean.__name__)


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
