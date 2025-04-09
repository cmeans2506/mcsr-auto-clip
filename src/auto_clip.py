import schedule
import time
from ranked_service import ranked_service
from obs_controller import obs_controller
from ffmpeg_service import  ffmpeg_service
from config import config
from bilibili_uploader import bilibili_uploader
from video_info_generator import VideoInfoGenerator

class AutoClip:
    def __init__(self):
        schedule.every(10).seconds.do(self._job)


    def _job(self):
        latest_match = ranked_service.get_latest_match()
        if latest_match is None:
            return

        raw_video_path = obs_controller.replay_save()
        print(f"存储了比赛[{latest_match.id_}]的录像：{raw_video_path}")

        cut_video_path = ffmpeg_service.auto_cut(match_info=latest_match, video_path=raw_video_path)
        # 用完，删掉
        raw_video_path.unlink()
        print(f"原始文件：{raw_video_path} 已删除")


        # 接下来是上传的逻辑
        def is_valid_for_upload():
            if latest_match.result.time > config.upload_setting[latest_match.type_.name].max_time:
                return False
            if latest_match.bastionType not in config.upload_setting[latest_match.type_.name].bastion_type:
                return False
            if latest_match.seedType not in config.upload_setting[latest_match.type_.name].seed_type:
                return False
            return True

        if not is_valid_for_upload():
            return

        match_data = ranked_service.get_match_data(latest_match.id_)
        user_data = ranked_service.get_user_data()

        video_info_generator = VideoInfoGenerator(
            match_data=match_data,
            match_info=latest_match,
            user_data=user_data,
            video_path=cut_video_path
        )
        bilibili_uploader.upload(video_info_generator.generate())


    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)  # 防止占用过多 CPU


auto_clip = AutoClip()
