import logging
import time
from ffmpeg_service import ffmpeg_service
from config import config
from bilibili_uploader import bilibili_uploader
from obs_controller import obs_controller
from apscheduler.schedulers.blocking import BlockingScheduler

from ranked.video_info_generator import VideoInfoGenerator as RankedVideoInfoGenerator
from ranked.ranked_service import ranked_service
from rsg.video_info_generator import VideoInfoGenerator as RsgVideoInfoGenerator
from rsg.paceman_service import paceman_service
from rsg.rsg_pb import rsg_pb
from logger import setup_logger

logger = setup_logger(__name__)
setup_logger('apscheduler', logging.WARNING)

class AutoClip:
    def __init__(self):
        self.blocking_scheduler = BlockingScheduler()
        self.blocking_scheduler.add_job(self._ranked_job, 'interval', seconds=10)
        self.blocking_scheduler.add_job(self._rsg_job, 'interval', seconds=10)
        if config.clean_raw_file:
            self.blocking_scheduler.add_job(obs_controller.clean, 'interval', minutes=2)
        if config.use_death_clip:
            self.blocking_scheduler.add_job(self._death_clip_job, 'interval', seconds=10)


    def _ranked_job(self):
        latest_match = ranked_service.get_latest_match()
        if latest_match is None:
            return

        raw_video_path = obs_controller.replay_save()
        logger.info(f"存储了比赛[{latest_match.id_}]的录像：{raw_video_path}")

        cut_video_path = ffmpeg_service.auto_cut(match_info=latest_match, video_path=raw_video_path)

        # 接下来是上传的逻辑
        if not latest_match.is_valid_for_upload():
            return

        match_data = ranked_service.get_match_data(latest_match.id_)
        user_data = ranked_service.get_user_data()

        video_info_generator = RankedVideoInfoGenerator(
            match_data=match_data,
            match_info=latest_match,
            user_data=user_data,
            video_path=cut_video_path
        )
        bilibili_uploader.upload(video_info_generator.generate())

    def _rsg_job(self):
        live_run = paceman_service.get_latest_run()
        if live_run is None:
            return

        if live_run.is_complete_run():
            logger.info(f"本场rsg速通是完整速通，等待{config.wait_for_datapack}秒用于输入/datapack list和/seed等指令...")
            time.sleep(config.wait_for_datapack)

        world_data = paceman_service.get_world(live_run.worldId)

        raw_video_path = obs_controller.replay_save()
        logger.info(f"存储了世界[{world_data.data.id}]的录像：{raw_video_path}")

        cut_video_path = ffmpeg_service.rsg_cut(live_run=live_run, world_data=world_data, video_path=raw_video_path)

        # 接下来是上传的逻辑
        if not live_run.is_valid_for_upload():
            return

        video_info_generator = RsgVideoInfoGenerator(
            live_run=live_run, world_data=world_data, video_path=cut_video_path
        )
        bilibili_uploader.upload(video_info_generator.generate())
        rsg_pb.check_for_pb(live_run=live_run, world_data=world_data)


    def _death_clip_job(self):
        latest_match_data = ranked_service.get_latest_death_match()
        if latest_match_data is None:
            return

        raw_video_path = obs_controller.replay_save()
        logger.info(f"存储了比赛[{latest_match_data.id_}]的录像：{raw_video_path}")

        cut_video_list = ffmpeg_service.death_clip(match_data=latest_match_data, video_path=raw_video_path)

        # 不上传

    def run(self):
        self.blocking_scheduler.start()


auto_clip = AutoClip()
